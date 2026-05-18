"""RouterAgent — classifies queries and routes to the appropriate sub-orchestrator.

Has fall-back mechanism:
- If MULTIPLE domains match → force fall-back (parallel query all specialists)
- If single domain with confidence >= 0.7 → direct route
- If confidence < 0.7 → fall-back
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from src.market_orchestrator.sub_orchestrator import BaseSubOrchestrator
from src.utils import get_logger

if TYPE_CHECKING:
    pass

log = get_logger("agents.router_agent")

_CONFIDENCE_THRESHOLD = 0.7


class RoutingDecision:
    """Result of routing a query."""
    
    def __init__(
        self,
        mode: str,
        sub_orchestrator: BaseSubOrchestrator | None = None,
        confidence: float = 0.0,
    ):
        self.mode = mode  # "direct" or "fallback"
        self.sub_orchestrator = sub_orchestrator
        self.confidence = confidence


class RouterAgent:
    """Routes queries to the correct sub-orchestrator based on domain."""
    
    def __init__(self) -> None:
        self.sub_orchestrators: list[BaseSubOrchestrator] = []
    
    def register(self, sub: BaseSubOrchestrator) -> None:
        """Register a sub-orchestrator."""
        self.sub_orchestrators.append(sub)
        log.info(f"🔄 Registered sub-orchestrator: {sub.domain}")
    
    def _get_domain_override(self, query_lower: str) -> str | None:
        """Detect explicit domain signals that should override routing.

        When the user mentions specific domain keywords, we want to ensure
        the query routes to the appropriate specialist, not to calculation.

        Returns:
            Domain name to force, or None if no override applies.
        """
        q = query_lower

        # Crypto override: if "crypto"/"cripto" mentioned, crypto takes priority
        # UNLESS explicit math terms indicate a calculation request
        has_crypto_signal = any(kw in q for kw in ["crypto", "cripto", "criptomoneda",
                                                     "bitcoin", "btc",
                                                     "ethereum", "eth", "blockchain",
                                                     "altcoin", "defi", "token"])
        has_math_signal = any(kw in q for kw in ["fórmula", "formula", "código", "codigo",
                                                   "script", "calculate", "cálculo",
                                                   "calcular", "compute", "npv",
                                                   "rentabilidad", "rendimiento", "porcentaje"]) or \
            any(kw in q for kw in [" tir ", " tir.", " tir,", " tir?"])
            # 'tir' requires word boundaries to avoid matching 'invertir'

        if has_crypto_signal and not has_math_signal:
            return "crypto"

        return None

    def route(self, query: str) -> RoutingDecision:
        """Classify query and return routing decision.

        Three possible outcomes:
        1. MULTI-TOPIC: if 2+ domains match → force fall-back
        2. DIRECT: single domain with confidence >= threshold
        3. FALL-BACK: no domain reaches threshold

        Domain override: explicit mentions (e.g. "crypto", "bitcoin") give
        priority to the matching specialist over generic matches.
        """
        if not self.sub_orchestrators:
            log.warning("⚠️ No sub-orchestrators registered!")
            return RoutingDecision(mode="fallback", confidence=0.0)

        log.info(f"🔍 Routing query: '{query[:100]}'")
        log.info(f"   Checking {len(self.sub_orchestrators)} sub-orchestrators:")

        matches = []  # (sub, confidence) for all that can_handle
        domain_map = {}  # domain_name -> (sub, conf)

        for sub in self.sub_orchestrators:
            can, conf = sub.can_handle(query)
            log.info(f"   {sub.domain:15s} → can_handle={can}, confidence={conf:.2f}")
            if can:
                matches.append((sub, conf))
                domain_map[sub.domain] = (sub, conf)

        # --- Domain override check ---
        override_domain = self._get_domain_override(query.lower())
        if override_domain and override_domain in domain_map:
            sub, conf = domain_map[override_domain]
            log.info(f"✅ DOMAIN OVERRIDE: '{override_domain}' forced by keyword signal")
            return RoutingDecision(
                mode="direct",
                sub_orchestrator=sub,
                confidence=max(conf, 0.75),
            )

        # Check for MULTI-TOPIC (2+ different domains match)
        if len(matches) >= 2:
            domains = [m[0].domain for m in matches]
            log.info(f"⚠️ MULTI-TOPIC detected: {domains} → forcing FALL-BACK")
            log.info("   Query touches multiple domains, consulting ALL specialists.")
            return RoutingDecision(mode="fallback", confidence=0.0)

        # Single match — pick best
        if matches:
            best_sub, best_conf = max(matches, key=lambda m: m[1])
            if best_conf >= _CONFIDENCE_THRESHOLD:
                log.info(f"✅ ROUTED TO '{best_sub.domain}' (confidence={best_conf:.2f})")
                return RoutingDecision(
                    mode="direct",
                    sub_orchestrator=best_sub,
                    confidence=best_conf,
                )
            else:
                log.info(f"⚠️ Single match but low confidence ({best_conf:.2f}) → FALL-BACK")
        else:
            log.info("⚠️ No sub-orchestrator matched → FALL-BACK")

        log.info("   All sub-orchestrators will be queried and results synthesized.")
        return RoutingDecision(mode="fallback", confidence=0.0)
    
    def answer(self, query: str) -> str:
        """Route the query and get an answer.
        
        Direct route: delegate to the best sub-orchestrator.
        Fall-back: query all, synthesize with LLM.
        """
        decision = self.route(query)
        
        if decision.mode == "direct" and decision.sub_orchestrator:
            log.info(f"▶️ Executing direct route: {decision.sub_orchestrator.domain}")
            return decision.sub_orchestrator.answer(query)
        
        # Fall-back: query all sub-orchestrators
        log.info(f"▶️ Executing FALL-BACK: querying ALL {len(self.sub_orchestrators)} sub-orchestrators")
        return self._fallback_answer(query)
    
    def _fallback_answer(self, query: str) -> str:
        """Query ALL sub-orchestrators and synthesize results."""
        results = []
        for sub in self.sub_orchestrators:
            try:
                log.info(f"   Querying {sub.domain}...")
                result = sub.answer(query)
                log.info(f"   {sub.domain} responded ({len(result)} chars)")
                results.append(f"--- {sub.domain.upper()} ---\n{result}")
            except Exception as e:
                log.warning(f"   {sub.domain} FAILED: {e}")
                results.append(f"--- {sub.domain.upper()} ---\nDatos no disponibles temporalmente.")
        
        combined = "\n\n".join(results)
        
        # Try LLM synthesis
        try:
            log.info("   Synthesizing results with LLM...")
            return self._synthesize_with_llm(query, combined)
        except Exception as e:
            log.warning(f"LLM synthesis failed: {e}")
            return combined
    
    def _synthesize_with_llm(self, query: str, context: str) -> str:
        """Use LLM to synthesize results from multiple domains."""
        try:
            from langchain_openai import ChatOpenAI
            from src.config import settings

            llm = ChatOpenAI(
                model=settings.rag_llm_model,
                temperature=0.3,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
            )

            prompt = f"""Sos un ASESOR FINANCIERO, no un programador. El usuario preguntó:

"{query}"

Recibiste información de MÚLTIPLES FUENTES. Sintetizala en una respuesta coherente y ejecutiva.

DATOS DISPONIBLES:
{context}

INSTRUCCIONES CRÍTICAS:
1. Actuá como ASESOR DE INVERSIONES. Dá RECOMENDACIONES, no código.
2. Si el usuario pregunta "en qué invertir" o busca consejo, sugerí activos concretos (ej: fracciones de BTC, ETH, acciones de AAPL, fondos indexados) con fundamento.
3. NUNCA generes código Python ni pidas al usuario que ejecute cálculos o scripts.
4. Integrá los datos de TODAS las fuentes disponibles en un análisis único.
5. Si una fuente devolvió datos, USALOS. No digas que no hay datos si los recibiste.
6. Si hay datos contradictorios, señalalos y explicá por qué.
7. Si una fuente específicamente dice "no disponible", simplemente no la menciones.
8. Respondé en el mismo idioma de la consulta.
9. Mencioná las fuentes: CoinMarketCap para crypto, FRED para macroeconomía.
10. Formato: narrativo, ejecutivo, en párrafos cortos. Sin código.

NUNCA digas "no tengo acceso a datos de X" si los datos están en el contexto arriba."""

            response = llm.invoke([
                {"role": "system", "content": "Sos un asesor financiero senior multi-mercado. Das RECOMENDACIONES DE INVERSIÓN y analizás activos. NUNCA generás código Python ni pedís al usuario que ejecute scripts. Tu objetivo es ACONSEJAR, no programar. Tenés acceso a CoinMarketCap (crypto), FRED (macroeconomía) y datos de mercado."},
                {"role": "user", "content": prompt},
            ])
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            log.warning("LLM synthesis failed: {}", e)
            return context
