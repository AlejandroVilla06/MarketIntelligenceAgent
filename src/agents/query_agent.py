"""
Query Agent - Market Query Agent with Dynamic Multi-Language Support
=====================================================================

LangChain ReAct agent wrapper for market data retrieval.
Automatically detects the user's language and responds in the same language.
Supports 55+ languages via langdetect.

Key improvements over v1:
- langdetect instead of keyword-based detection (supports 55+ languages)
- Single dynamic prompt with {language} parameter instead of ES/EN copies
- Temperature 0.3 for varied natural responses (was 0.0 deterministic)
- No regex post-processing — LLM is instructed to skip ReAct format
- Greetings and errors adapt to detected language

Usage:
    from src.agents.query_agent import MarketQueryAgent
    agent = MarketQueryAgent(retriever)
    answer = agent.run("Comment se porte l'action Apple?")  # responds in French
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

from langchain_openai import ChatOpenAI

from src.agents.chains.prompts import build_agent_prompt, build_analysis_prompt, build_summarize_prompt
from src.agents.memory.conversation import ConversationMemory
from src.agents.user_context import ctx as user_ctx, get_profile_string, get_technical_level_instruction
from src.config import settings
from src.utils import get_logger

if TYPE_CHECKING:
    from src.agents.retriever import MarketRAGRetriever

log = get_logger("agents.query_agent")


# =============================================================================
# LANGUAGE DETECTION — langdetect with keyword fallback
# =============================================================================


@functools.lru_cache(maxsize=128)
def detect_language(query: str) -> str:
    """Detect the language of a user query using langdetect.

    Supports 55+ languages via the langdetect library (Google's language-detection port).
    Falls back to keyword-based detection if langdetect is unavailable.

    Args:
        query: User's query string

    Returns:
        ISO 639-1 language code (e.g., 'en', 'es', 'fr', 'de', 'pt', 'it').
        Returns 'en' as default fallback.
    """
    if not query or not query.strip():
        return "en"

    # --- Keyword-based detection runs FIRST for 6 known languages ---
    # langdetect is unreliable on short/mixed queries (e.g., "hola how are you" → Somali).
    # If keyword matching finds a clear winner, we use it directly.
    # If keyword matching is inconclusive AND the query is long enough, fall through to langdetect.
    keyword_result = _keyword_detect(query)

    # If keyword detection found a clear winner (score > 0), use it
    if keyword_result is not None:
        return keyword_result

    # Keyword detection was inconclusive — try langdetect for longer queries
    try:
        import langdetect

        try:
            lang = langdetect.detect(query)
            if lang and len(lang) == 2:
                return lang
        except langdetect.lang_detect_exception.LangDetectException:
            pass
    except ImportError:
        log.debug("langdetect not installed")
    except Exception:
        log.debug("langdetect failed")

    return "en"


def _keyword_detect(query: str) -> str | None:
    """Detect language using keyword matching for 6 known languages.

    Returns:
        ISO 639-1 code if a clear winner is found, None if uncertain.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return "en"
    query_lower = query.lower().strip()

    english_words = [
        "hello", "hi", "hey", "how", "what", "when", "where", "who",
        "can", "could", "would", "should", "need", "want", "help",
        "thanks", "please", "stock", "stocks", "market", "news",
        "price", "volume", "investment", "portfolio", "share", "shares",
        "the", "this", "that", "with", "from", "have", "been", "were",
    ]
    spanish_words = [
        "hola", "buenos", "buenas", "cómo", "como", "estás", "estas",
        "qué", "que", "dime", "necesito", "quiero", "puedo", "ayúdame",
        "ayuda", "gracias", "por favor", "cuál", "cual", "cuándo", "cuando",
        "dónde", "donde", "quién", "quien", "acciones", "bolsa", "mercado",
        "noticias", "sentimiento", "precio", "volumen", "inversión", "invertir",
        "puedes", "estar", "sobre", "pero", "más", "bien",
    ]
    french_words = [
        "bonjour", "salut", "bonsoir", "comment", "puis", "aide", "merci",
        "s'il vous plaît", "stock", "action", "marché", "nouvelles", "sentiment",
        "prix", "volume", "investissement", "quelle", "qu'est-ce", "pourrais",
        "voulez", "ça", "va", "être", "dans", "avec", "faire", "peux",
        "comment", "trouver", "montre",
    ]
    german_words = [
        "hallo", "guten", "tag", "bitte", "danke", "wie", "was", "ist",
        "aktie", "aktien", "kurs", "markt", "nachrichten", "sentiment",
        "preis", "volumen", "investition", "zeig", "mir", "kannst",
    ]
    portuguese_words = [
        "olá", "bom", "dia", "como", "vai", "ajuda", "obrigado", "por favor",
        "ação", "ações", "mercado", "notícias", "sentimento", "preço", "volume",
        "investimento", "qual", "pode", "quero", "preciso", "esta", "estar",
        "hoje", "sobre", "para", "mais", "bem", "muito", "tudo", "não",
        "coisa", "coisas", "são", "pelos", "pelas", "entre", "depois",
    ]
    italian_words = [
        "ciao", "buongiorno", "come", "stai", "aiuto", "grazie", "per favore",
        "azione", "azioni", "mercato", "notizie", "sentimento", "prezzo", "volume",
        "investimento", "quale", "puoi", "voglio", "mostra",
    ]

    import re

    def score(words: list[str]) -> int:
        return sum(1 for w in words if w in query_lower)

    scores = {
        "en": score(english_words),
        "es": score(spanish_words),
        "fr": score(french_words),
        "de": score(german_words),
        "pt": score(portuguese_words),
        "it": score(italian_words),
    }

    # Boost scores for language-specific character patterns
    # Portuguese gets extra boost for "ão"/"õe" which are uniquely Portuguese
    if re.search(r'[áéíóúüñ]', query_lower):
        scores["es"] += 3
    if re.search(r'[àâçéèêëîïôûùü]', query_lower):
        scores["fr"] += 3
    if re.search(r'[äöüß]', query_lower):
        scores["de"] += 3
    if re.search(r'[ãõáéíóúâêîôûç]', query_lower):
        scores["pt"] += 3
    if re.search(r'[ãõ]', query_lower):
        scores["pt"] += 5  # "ão" and "õe" are uniquely Portuguese
    if re.search(r'[àèéìíîòóù]', query_lower):
        scores["it"] += 3

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    # Nothing matched — default to English
    return "en"


# =============================================================================
# MULTI-LANGUAGE GREETINGS
# =============================================================================

# Greeting templates indexed by ISO 639-1 code
_GREETINGS: dict[str, str] = {
    "en": (
        "👋 Hello! Great to see you here. I'm your market analysis assistant. "
        "I can help you understand stock behavior, the latest financial news, "
        "and market sentiment. How can I help you today?"
    ),
    "es": (
        "👋 ¡Hola! Me alegra verte por aquí. Soy tu asistente de análisis de mercado. "
        "Puedo ayudarte a entender el comportamiento de las acciones, las últimas noticias "
        "financieras y el sentimiento del mercado. ¿En qué puedo ayudarte hoy?"
    ),
    "fr": (
        "👋 Bonjour ! Ravi de vous voir ici. Je suis votre assistant d'analyse de marché. "
        "Je peux vous aider à comprendre le comportement des actions, les dernières actualités "
        "financières et le sentiment du marché. Comment puis-je vous aider aujourd'hui ?"
    ),
    "de": (
        "👋 Hallo! Schön, dass Sie hier sind. Ich bin Ihr Marktanalyse-Assistent. "
        "Ich kann Ihnen helfen, das Verhalten von Aktien, die neuesten Finanznachrichten "
        "und die Marktstimmung zu verstehen. Wie kann ich Ihnen heute helfen?"
    ),
    "pt": (
        "👋 Olá! Que bom ver você aqui. Sou seu assistente de análise de mercado. "
        "Posso ajudá-lo a entender o comportamento das ações, as últimas notícias "
        "financeiras e o sentimento do mercado. Como posso ajudar hoje?"
    ),
    "it": (
        "👋 Ciao! Sono felice di vederti qui. Sono il tuo assistente di analisi di mercato. "
        "Posso aiutarti a capire il comportamento delle azioni, le ultime notizie "
        "finanziarie e il sentiment del mercato. Come posso aiutarti oggi?"
    ),
}

_CONCERN_RESPONSES: dict[str, str] = {
    "en": "I understand your concern. Let me look into that information for you.",
    "es": "Entiendo tu preocupación. Déjame buscar esa información para ti.",
    "fr": "Je comprends votre préoccupation. Laissez-moi chercher cette information pour vous.",
    "de": "Ich verstehe Ihre Besorgnis. Lassen Sie mich diese Information für Sie suchen.",
    "pt": "Entendo sua preocupação. Deixe-me buscar essa informação para você.",
    "it": "Capisco la tua preoccupazione. Lascia che cerchi queste informazioni per te.",
}

_ERROR_MESSAGES: dict[str, str] = {
    "en": "I encountered an error processing your query. Please try again.",
    "es": "Encontré un error al procesar tu consulta. Por favor intenta de nuevo.",
    "fr": "J'ai rencontré une erreur lors du traitement de votre requête. Veuillez réessayer.",
    "de": "Bei der Verarbeitung Ihrer Anfrage ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.",
    "pt": "Encontrei um erro ao processar sua consulta. Por favor, tente novamente.",
    "it": "Ho riscontrato un errore durante l'elaborazione della richiesta. Per favore riprova.",
}

_NO_DATA_MESSAGES: dict[str, str] = {
    "en": "No documents indexed. Please run data ingestion first.",
    "es": "No hay documentos indexados. Por favor ejecuta la ingestión de datos primero.",
    "fr": "Aucun document indexé. Veuillez d'abord exécuter l'ingestion de données.",
    "de": "Keine Dokumente indiziert. Bitte führen Sie zuerst die Datenerfassung aus.",
    "pt": "Nenhum documento indexado. Execute a ingestão de dados primeiro.",
}

_NO_RESULTS_MESSAGES: dict[str, str] = {
    "en": "No results found for your query. Try asking about specific stocks like 'AAPL' or 'NVDA'.",
    "es": "No encontré resultados. Prueba preguntando por acciones específicas como 'AAPL' o 'NVDA'.",
    "fr": "Aucun résultat trouvé. Essayez de demander des actions spécifiques comme 'AAPL' ou 'NVDA'.",
    "de": "Keine Ergebnisse gefunden. Fragen Sie nach bestimmten Aktien wie 'AAPL' oder 'NVDA'.",
    "pt": "Nenhum resultado encontrado. Tente perguntar sobre ações específicas como 'AAPL' ou 'NVDA'.",
}


def _localize(dictionary: dict[str, str], language: str) -> str:
    """Get a localized string from a dictionary, falling back to English."""
    return dictionary.get(language, dictionary.get("en", ""))


def get_empathetic_greeting(language: str) -> str:
    """Return a greeting in the detected language.

    Args:
        language: ISO 639-1 language code

    Returns:
        Localized greeting string
    """
    return _localize(_GREETINGS, language)


def get_empathetic_concern_response(language: str) -> str:
    """Return a concern acknowledgment in the detected language.

    Args:
        language: ISO 639-1 language code

    Returns:
        Localized response string
    """
    return _localize(_CONCERN_RESPONSES, language)


# =============================================================================
# MARKET QUERY AGENT
# =============================================================================


class MarketQueryAgent:
    """LangChain ReAct agent for market queries with dynamic multi-language support.

    Automatically detects the user's language and builds a prompt that instructs
    the LLM to respond in that language. Tool descriptions remain in English.

    Key improvements over v1:
    - Single dynamic prompt with {language} parameter
    - Temperature 0.3 (was 0.0) for natural variation
    - No regex post-processing of responses
    - 55+ language support

    Usage:
        agent = MarketQueryAgent(retriever)
        answer = agent.run("How did AAPL news affect stock price?")
        answer = agent.run("Comment se porte l'action Apple?")
    """

    def __init__(
        self,
        retriever: MarketRAGRetriever | None = None,
        model_name: str | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        """Initialize the two-stage retrieval + analysis agent.

        Stage 1: Retrieve raw data from ChromaDB via the retriever.
        Stage 2: Send retrieved data + System Prompt to the LLM for executive analysis.

        Args:
            retriever: MarketRAGRetriever instance (creates new if None)
            model_name: LLM model name (default: settings.rag_llm_model)
            temperature: LLM temperature (default: settings.rag_llm_temperature)
            max_retries: Max retries on error (default: settings.rag_max_retries)
        """
        self.model_name = model_name or settings.rag_llm_model
        self.temperature = temperature if temperature is not None else settings.rag_llm_temperature
        self.max_retries = max_retries or settings.rag_max_retries

        # Retriever is lazily created when first needed
        self._retriever = retriever
        self._retriever_initialized = retriever is not None

        # Initialize conversation memory
        self.memory = ConversationMemory()

        # Initialize LLM — supports OpenAI, DeepSeek, or any OpenAI-compatible API
        self._llm = self._init_llm()

    def _init_llm(self) -> Any | None:
        """Initialize the LLM based on the configured provider.

        Supports:
        - 'openai' → OpenAI API (settings.openai_api_key)
        - 'deepseek' → DeepSeek API (settings.deepseek_api_key)
        - Any OpenAI-compatible API by configuring the provider settings.

        Returns:
            ChatOpenAI instance, or None if no API key is configured.
        """
        provider = settings.llm_provider

        if provider == "deepseek":
            api_key = settings.deepseek_api_key
            model = settings.deepseek_model
            base_url = settings.deepseek_api_base
            log.info(f"Using DeepSeek provider: model={model}, base_url={base_url}")
        else:
            api_key = settings.openai_api_key
            model = self.model_name
            # If openai_api_base is set (e.g. OpenCode Go endpoint), use it
            base_url = settings.openai_api_base
            log.info(f"Using OpenAI provider: model={model}" + (f", base_url={base_url}" if base_url else ""))

        if not api_key:
            log.warning(f"No API key found for provider '{provider}'. Using fallback mode.")
            return None

        kwargs = {
            "model": model,
            "temperature": self.temperature,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOpenAI(**kwargs)

    @property
    def retriever(self) -> Any:
        """Lazy-initialized MarketRAGRetriever."""
        if not self._retriever_initialized:
            try:
                from src.agents.retriever import MarketRAGRetriever as _MRR
                self._retriever = _MRR()
            except ImportError as e:
                log.warning(f"Could not import MarketRAGRetriever: {e}")
                self._retriever = None
            self._retriever_initialized = True
        return self._retriever

    # =========================================================================
    # TWO-STAGE PIPELINE
    # =========================================================================

    def run(self, query: str) -> str:
        """Two-stage pipeline: retrieve → analyze.

        Stage 1 — _retrieve_raw_data(): Queries ChromaDB and stores results.
        Stage 2 — _generate_analysis(): Passes raw data + system prompt to LLM.

        Args:
            query: User's question (any language supported)

        Returns:
            Executive analysis in the detected language.
            NEVER raw data dumps.
        """
        language = detect_language(query)
        self.memory.add_user_message(query)

        # --- Greeting quick-check ---
        if self._is_greeting(query):
            greeting = get_empathetic_greeting(language)
            self.memory.add_ai_message(greeting)
            return greeting

        # --- Cache check ---
        cached = self._check_cache(query, language)
        if cached is not None:
            self.memory.add_ai_message(cached)
            return cached

        # --- STAGE 1: Retrieve raw data from ChromaDB ---
        log.info(f"[Stage 1] Retrieving data for: {query[:60]}...")
        chroma_data = self._retrieve_raw_data(query)
        log.info(f"[Stage 1] Retrieved data: {type(chroma_data).__name__}")

        # Handle empty data
        if self._is_empty(chroma_data):
            msg = _localize(_NO_RESULTS_MESSAGES, language)
            self.memory.add_ai_message(msg)
            return msg

        # --- STAGE 2: Generate executive analysis via LLM ---
        log.info("[Stage 2] Generating executive analysis...")

        if self._llm is not None:
            result = self._generate_analysis(query, chroma_data, language)
        else:
            # No LLM available → fallback formatting
            log.warning("No LLM available. Using fallback formatting.")
            result = self._format_output(chroma_data)

        # --- Post-processing: strip any artifacts the LLM might leak ---
        result = self._strip_react_artifacts(result)
        result = self._strip_data_sections(result)
        self.memory.add_ai_message(result)

        # Cache the result
        self._store_cache(query, result, language)

        return result

    async def run_stream(self, query: str):
        """Async generator: retrieve → stream analysis tokens.

        Same two-stage pipeline as run(), but Stage 2 streams tokens
        from the LLM via astream() instead of waiting for the full response.

        Yields:
            str: tokens as they arrive from the LLM
        """
        language = detect_language(query)
        self.memory.add_user_message(query)

        # --- Greeting quick-check ---
        if self._is_greeting(query):
            greeting = get_empathetic_greeting(language)
            self.memory.add_ai_message(greeting)
            yield greeting
            return

        # --- Cache check ---
        cached = self._check_cache(query, language)
        if cached is not None:
            self.memory.add_ai_message(cached)
            yield cached
            return

        # --- STAGE 1: Retrieve raw data from ChromaDB ---
        log.info(f"[Stage 1] Retrieving data for: {query[:60]}...")
        chroma_data = self._retrieve_raw_data(query)

        if self._is_empty(chroma_data):
            msg = _localize(_NO_RESULTS_MESSAGES, language)
            self.memory.add_ai_message(msg)
            yield msg
            return

        # --- STAGE 2: Stream analysis tokens from LLM ---
        log.info("[Stage 2] Streaming analysis...")

        if self._llm is None:
            yield self._format_output()
            return

        # Build prompts (same as _generate_analysis)
        system_text = build_analysis_prompt(
            language=language,
            chat_history=self.memory.get_context_string(),
            user_context=get_profile_string(),
            technical_level_instruction=get_technical_level_instruction(),
            technical_level=user_ctx.technical_level,
        )
        formatted_data = self._format_data_for_prompt(chroma_data)
        user_message = f"""USER QUESTION: {query}

--- SILENT CONTEXT (market data - use for analysis only, do NOT reproduce) ---
{formatted_data}
--- END SILENT CONTEXT ---

Remember: Respond ONLY with executive analysis. Never include the data above."""

        messages = [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_message},
        ]

        full_response = ""
        try:
            async for chunk in self._llm.astream(messages):
                token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                if token:
                    full_response += token
                    yield token
        except Exception as e:
            log.error(f"LLM streaming failed: {e}")
            yield f"\n\n[Error durante el streaming: {e}]"
            return

        # Post-processing (same as run())
        full_response = self._strip_react_artifacts(full_response)
        full_response = self._strip_data_sections(full_response)
        self.memory.add_ai_message(full_response)
        self._store_cache(query, full_response, language)

    def _is_greeting(self, query: str) -> bool:
        """Quick check if the query is just a greeting."""
        q = query.lower().strip()
        greetings = {"hola", "hello", "hi", "hey", "bonjour", "salut", "olá",
                     "buenos días", "buenas", "qué tal", "como estas", "saludos",
                     "guten tag", "hallo", "ciao", "bom dia"}
        if q in greetings:
            return True
        for prefix in ["hola", "hello", "hi ", "bonjour", "guten"]:
            if q.startswith(prefix):
                return True
        return False

    def _check_cache(self, query: str, language: str) -> str | None:
        """Check semantic cache. Returns sanitized cached result or None.
        
        Before returning, sanitizes the output through _strip_data_sections()
        to prevent cached raw data from reaching the user.
        """
        if not getattr(settings, 'cache_enabled', False):
            return None
        try:
            from src.agents.cache import get_cache_instance
            cache = get_cache_instance()
            model_id = f"{settings.llm_provider}/{self.model_name}"
            params = {"temperature": self.temperature, "language": language}
            result = cache.get(query, model_id=model_id, model_params=params)
            if result:
                # Sanitize before returning — prevent cached raw data leaks
                sanitized = self._strip_data_sections(str(result))
                if len(sanitized) < 50:
                    # Result was mostly data sections, invalidate
                    log.info(f"Cache HIT but sanitized result too short ({len(sanitized)} chars). Invalidating.")
                    return None
                log.info(f"Cache HIT: {query[:50]}...")
                return sanitized
            return None
        except Exception as e:
            log.warning(f"Cache lookup failed: {e}")
            return None

    def _store_cache(self, query: str, result: str, language: str) -> None:
        """Store result in semantic cache."""
        if not getattr(settings, 'cache_enabled', False):
            return
        try:
            from src.agents.cache import get_cache_instance
            cache = get_cache_instance()
            model_id = f"{settings.llm_provider}/{self.model_name}"
            params = {"temperature": self.temperature, "language": language}
            cache.set(query, result, model_id=model_id, model_params=params)
        except Exception as e:
            log.warning(f"Cache store failed: {e}")

    # =========================================================================
    # STAGE 1: Raw data retrieval from ChromaDB
    # =========================================================================

    def _retrieve_raw_data(self, query: str) -> Any:
        """Query ChromaDB and return ALL raw results.

        This is Stage 1 of the pipeline. Results are stored in a variable
        and passed to Stage 2 for analysis. Never displayed to the user raw.

        Returns:
            Dict with keys 'stocks', 'news', 'sentiment' (each a list of dicts),
            or a list for single-collection queries.
        """
        if self.retriever is None:
            log.error("Retriever is None")
            return {}

        try:
            counts = {
                "stocks": self.retriever._stocks_collection.count(),
                "news": self.retriever._news_collection.count(),
                "sentiment": self.retriever._sentiment_collection.count(),
            }
            if sum(counts.values()) == 0:
                log.warning("ChromaDB collections are empty")
                return {}
        except Exception as e:
            log.error(f"Error checking counts: {e}")

        # Query ALL collections — the LLM will decide what's relevant
        query_lower = query.lower()
        if any(w in query_lower for w in ["news", "article", "headline", "noticia", "actualité"]):
            return {"news": self.retriever.query_news(query)}
        elif any(w in query_lower for w in ["sentiment", "mood", "feeling", "sentimiento", "sentimento"]):
            return {"sentiment": self.retriever.query_sentiment(query)}
        elif any(w in query_lower for w in ["stock", "price", "volume", "rsi", "acción", "preço", "cours"]):
            return {"stocks": self.retriever.query_stocks(query)}
        else:
            return self.retriever.query_all(query)

    @staticmethod
    def _is_empty(data: Any) -> bool:
        """Check if retrieved data is empty."""
        if not data:
            return True
        if isinstance(data, dict):
            return sum(len(v) for v in data.values() if isinstance(v, list)) == 0
        if isinstance(data, list):
            return len(data) == 0
        return False

    # =========================================================================
    # STAGE 2: Executive analysis via LLM
    # =========================================================================

    def _generate_analysis(self, query: str, chroma_data: Any, language: str) -> str:
        """Generate executive analysis using clean prompt + Silent Context.
        
        Uses build_analysis_prompt() instead of build_agent_prompt() + regex stripping.
        The system prompt is clean (no ReAct artifacts). Data goes as Silent Context
        in the user message.
        
        Args:
            query: Original user question
            chroma_data: Raw data from ChromaDB (Stage 1 output)
            language: ISO 639-1 language code
        
        Returns:
            Executive analysis string. NEVER raw data.
        """
        # Build the clean system prompt (NO ReAct artifacts)
        system_text = build_analysis_prompt(
            language=language,
            chat_history=self.memory.get_context_string(),
            user_context=get_profile_string(),
            technical_level_instruction=get_technical_level_instruction(),
            technical_level=user_ctx.technical_level,
        )

        # Format the raw data for prompt inclusion (Silent Context)
        formatted_data = self._format_data_for_prompt(chroma_data)

        # Build the user message with data as Silent Context
        user_message = f"""USER QUESTION: {query}

--- SILENT CONTEXT (market data - use for analysis only, do NOT reproduce) ---
{formatted_data}
--- END SILENT CONTEXT ---

Remember: Respond ONLY with executive analysis. Never include the data above."""

        # Send to LLM
        messages = [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_message},
        ]

        try:
            response = self._llm.invoke(messages)
            result = response.content if hasattr(response, 'content') else str(response)
            # Safety net: strip any remaining data sections the LLM might leak
            result = self._strip_data_sections(result)
            return result
        except Exception as e:
            log.error(f"LLM analysis generation failed: {e}")
            return self._format_output()

    @staticmethod
    def _format_data_for_prompt(data: Any) -> str:
        """Format raw ChromaDB data into a structured text block for the LLM prompt.

        Uses NEUTRAL markers (not English) so the LLM doesn't get confused
        about what language to output. The LLM must translate everything.
        This data is NEVER shown to the user directly.
        """
        if not data:
            return "No data available."

        parts = []

        if isinstance(data, dict):
            # Collect symbols found
            symbols = set()
            for coll, items in data.items():
                if isinstance(items, list):
                    for item in items:
                        meta = item.get("metadata", {})
                        if sym := meta.get("symbol"):
                            symbols.add(sym)

            if symbols:
                parts.append(f"Tickers: {', '.join(sorted(symbols))}")

            # Neutral section headers — no English words that leak language
            for section_key, section_label in [("stocks", "PRICE"), ("news", "NEWS"), ("sentiment", "SENTIMENT")]:
                items = data.get(section_key, [])
                if not items:
                    continue

                parts.append(f"\n--- {section_label} ---")
                for i, item in enumerate(items[:8]):
                    doc = item.get("document", "")
                    meta = item.get("metadata", {})
                    # Only include non-null metadata
                    meta_items = [f"{k}={v}" for k, v in meta.items() if v is not None]
                    meta_str = "; ".join(meta_items)
                    # Truncate document for prompt length
                    doc_trunc = doc[:250] if doc else ""
                    parts.append(f"  [{i + 1}] {doc_trunc}")
                    if meta_str:
                        parts.append(f"       [{meta_str}]")

        elif isinstance(data, list):
            parts.append(f"Records: {len(data)}")
            for i, item in enumerate(data[:8]):
                doc = item.get("document", "")
                meta = item.get("metadata", {})
                meta_items = [f"{k}={v}" for k, v in meta.items() if v is not None]
                meta_str = "; ".join(meta_items)
                doc_trunc = doc[:250] if doc else ""
                parts.append(f"  [{i + 1}] {doc_trunc}")
                if meta_str:
                    parts.append(f"       [{meta_str}]")
        else:
            parts.append(str(data)[:1000])

        return "\n".join(parts)

    @staticmethod
    def _strip_react_artifacts(text: str) -> str:
        """Safety net: strip any ReAct loop artifacts the LLM might leak."""
        import re
        prefixes = [
            r'^Thought:\s*', r'^Action:\s*', r'^Action Input:\s*',
            r'^Observation:\s*', r'^Answer:\s*', r'^Question:\s*',
            r'^Final Answer:\s*',
        ]
        for prefix in prefixes:
            text = re.sub(prefix, '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(
            r'^(Thought|Action|Action Input|Observation|Answer|Question|Final Answer):.*$',
            '', text, flags=re.IGNORECASE | re.MULTILINE
        )
        text = text.replace('Begin!', '').replace('begin!', '')
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def _strip_data_sections(text: str) -> str:
        """Safety net: remove any raw data sections from LLM output.
        
        Covers patterns in 6 languages (es, en, fr, de, pt, it).
        This is a defense-in-depth layer — the primary defense is the clean prompt.
        """
        import re
        
        # Section headers in all supported languages (#/##/### Markdown headings)
        section_patterns = [
            # Spanish
            r'^#*\s*(Datos de Precio|Precio|Precios|Noticias|Sentimiento|Sentimiento del Mercado|Acciones|Resumen de|Análisis Técnico).*$',
            # English
            r'^#*\s*(Price Data|Price|Prices|News|Market Sentiment|Sentiment|Stocks|Stock Data|Technical Analysis|Market Data|Recent News|Executive Summary).*$',
            # French
            r'^#*\s*(Données de Prix|Prix|Actualités|Nouvelles|Sentiment|Sentiment du Marché|Actions|Résumé).*$',
            # German
            r'^#*\s*(Preisdaten|Preis|Nachrichten|Stimmung|Marktstimmung|Aktien|Zusammenfassung).*$',
            # Portuguese
            r'^#*\s*(Dados de Preço|Preço|Notícias|Sentimento|Sentimento do Mercado|Ações|Resumo).*$',
            # Italian
            r'^#*\s*(Dati di Prezzo|Prezzo|Notizie|Sentimento|Sentimento del Mercato|Azioni|Riepilogo).*$',
        ]
        
        for pattern in section_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Markdown section dividers
        text = re.sub(r'^---+\s*(PRICE|NEWS|SENTIMENT|DATA|MARKET)\s*---+\s*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Lines with bold section labels (common LLM pattern)
        text = re.sub(r'^\*\*(Price Data|Recent News|Market Sentiment|Datos de Precio|Noticias|Sentimiento)\*\*.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Markdown tables (data often leaks as tables)
        text = re.sub(r'^\|.*\|$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\|?\s*:?-+:?\s*\|?$', '', text, flags=re.MULTILINE)
        
        # Lines with just "key: value" patterns that look like raw data
        text = re.sub(r'^\s*(close|volume|price|sentiment|score|rsi|open|high|low)\s*[:=]\s*\d+[\d.,]*\s*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Numbered data lines like "[1] AAPL 2024-01-15 close=170.2"
        text = re.sub(r'^\s*\[\d+\].*$', '', text, flags=re.MULTILINE)
        
        # Lines with ticker + date patterns (common in raw data)
        text = re.sub(r'^\s*[A-Z]{1,5}\s+\d{4}[-/]\d{2}[-/]\d{2}.*$', '', text, flags=re.MULTILINE)
        
        # Data section delimiters
        text = re.sub(r'^---\s*(BEGIN|END)\s+(DATA|SILENT CONTEXT|CONTEXT)\s*---\s*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # "SILENT CONTEXT" or "Context" labels that might leak
        text = re.sub(r'^SILENT CONTEXT.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'^---.*DATA.*---$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove empty/whitespace-only lines and collapse multiple blank lines
        lines = [line for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    @staticmethod
    def _format_output(data: Any = None) -> str:
        """Fallback — used ONLY when NO LLM is available.
        
        NEVER reveals what data was found. Generic message.
        
        Args:
            data: Ignored (included for backward compatibility)
        
        Returns:
            Generic message about LLM configuration
        """
        return (
            "No fue posible generar el análisis ejecutivo en este momento.\n\n"
            "Esto puede deberse a que el modelo de lenguaje no está configurado.\n\n"
            "Para habilitar el análisis, configurá tu API key en el archivo `.env`:\n"
            "- `LLM_PROVIDER=deepseek` y `DEEPSEEK_API_KEY=tu_key` (DeepSeek)\n"
            "- o `OPENAI_API_KEY=tu_key` (OpenAI)\n\n"
            "Una vez configurado, reiniciá la aplicación y volvé a preguntar."
        )

    def reset(self) -> None:
        """Reset agent state (clear memory)."""
        self.memory.clear()


__all__ = [
    "MarketQueryAgent",
    "detect_language",
    "get_empathetic_greeting",
    "get_empathetic_concern_response",
]