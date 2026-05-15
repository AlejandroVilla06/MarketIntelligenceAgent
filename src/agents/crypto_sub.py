"""CryptoSubOrchestrator — cryptocurrency data via CoinMarketCap + LLM analysis."""
from __future__ import annotations
from src.agents.sub_orchestrator import BaseSubOrchestrator
from src.utils import get_logger

log = get_logger("agents.crypto_sub")

_CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
    "solana", "sol", "xrp", "cardano", "ada", "polkadot", "dot",
    "dogecoin", "doge", "avalanche", "avax", "chainlink", "link",
    "polygon", "matic", "uniswap", "uni", "coin", "token",
    "blockchain", "defi", "nft", "mining", "wallet", "exchange",
    "market cap", "altcoin", "stablecoin", "usdt", "usdc",
]


class CryptoSubOrchestrator(BaseSubOrchestrator):
    """Handles cryptocurrency queries via CoinMarketCap + LLM analysis."""
    
    def __init__(self) -> None:
        self._llm = None
    
    def _get_llm(self):
        """Lazy-init LLM for formatting responses."""
        if self._llm is None:
            try:
                from langchain_openai import ChatOpenAI
                from src.config import settings
                self._llm = ChatOpenAI(
                    model=settings.rag_llm_model,
                    temperature=0.3,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_api_base,
                )
            except Exception as e:
                log.warning(f"Could not init LLM for crypto: {e}")
                self._llm = False  # Sentinel
        return self._llm if self._llm is not False else None
    
    def _analyze_with_llm(self, query: str, data: str) -> str:
        """Format raw crypto data into natural language analysis via LLM."""
        llm = self._get_llm()
        if not llm:
            return data  # Fallback to raw data if no LLM
        
        try:
            prompt = f"""Sos un analista de criptomonedas. El usuario preguntó:

"{query}"

DATOS EN TIEMPO REAL (CoinMarketCap):
{data}

Instrucciones:
- Respondé en el mismo idioma de la consulta
- Analizá los datos como un analista financiero, no los listes crudos
- Incluí contexto: ¿el precio subió o bajó? ¿qué implica?
- Mencioná fuentes: CoinMarketCap para datos en tiempo real
- Formato: narrativo, ejecutivo, en párrafos cortos"""
            
            response = llm.invoke([
                {"role": "system", "content": "Sos un analista de criptomonedas con datos en tiempo real de CoinMarketCap."},
                {"role": "user", "content": prompt},
            ])
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            log.warning(f"LLM crypto analysis failed: {e}")
            return data
    
    @property
    def domain(self) -> str:
        return "crypto"
    
    def can_handle(self, query: str) -> tuple[bool, float]:
        q = query.lower().strip()
        if not q:
            return False, 0.0
        
        matches = sum(1 for kw in _CRYPTO_KEYWORDS if kw in q)
        if matches >= 2:
            return True, 0.95
        elif matches >= 1:
            return True, 0.80
        return False, 0.0
    
    def _get_crypto_data(self, query: str) -> str:
        """Lazy import and call crypto MCP functions."""
        # Lazy import — MCP package takes ~1.4s to load
        from src.agents.mcp.crypto_server import get_crypto_price, get_top_cryptos, get_crypto_global_metrics
        
        q = query.lower()
        
        if "global" in q or ("market" in q and any(c in q for c in ["total", "overview", "cap"])):
            return get_crypto_global_metrics()

        if "top" in q or "leading" in q or "ranking" in q:
            return get_top_cryptos(10)

        known_coins = {
            "btc": "BTC", "bitcoin": "BTC",
            "eth": "ETH", "ethereum": "ETH",
            "sol": "SOL", "solana": "SOL",
            "xrp": "XRP", "ripple": "XRP",
            "ada": "ADA", "cardano": "ADA",
            "doge": "DOGE", "dogecoin": "DOGE",
            "dot": "DOT", "polkadot": "DOT",
            "avax": "AVAX", "avalanche": "AVAX",
            "link": "LINK", "chainlink": "LINK",
            "matic": "MATIC", "polygon": "MATIC",
            "uni": "UNI", "uniswap": "UNIP",
        }

        for name, symbol in known_coins.items():
            if name in q:
                return get_crypto_price(symbol)

        return get_top_cryptos(10)

    def answer(self, query: str) -> str:
        try:
            raw_data = self._get_crypto_data(query)
            return self._analyze_with_llm(query, raw_data)
        except Exception as e:
            log.error(f"CryptoSubOrchestrator failed: {e}")
            return f"📡 **Datos Crypto en tiempo real**\n\n_CoinMarketCap consultado exitosamente._\n\nError al procesar: {e}"
