"""StocksSubOrchestrator — wraps the existing MarketQueryAgent pipeline."""
from __future__ import annotations
from src.market_orchestrator.sub_orchestrator import BaseSubOrchestrator
from src.utils import get_logger

log = get_logger("agents.stocks_sub")

_STOCK_KEYWORDS = [
    # English
    "stock", "stocks", "market", "equity", "equities", "share", "shares",
    "aapl", "msft", "googl", "nvda", "amzn", "tsla", "meta",
    "price", "volume", "rsi", "market cap", "pe ratio", "dividend",
    "earnings", "revenue", "profit", "sec filing", "ipo",
    "invest", "investment", "portfolio", "strategy",
    # Spanish
    "acción", "acciones", "accion", "acciones", "bolsa", "precio", "cotización",
    "invertir", "inversión", "inversion", "invierta", "invierto",
    "cartera", "portafolio", "estrategia", "comprar", "vender", "recomienda", "recomiendas",
]


class StocksSubOrchestrator(BaseSubOrchestrator):
    """Wraps the existing MarketQueryAgent for stock/equity queries.
    
    Zero changes to the existing pipeline — this is a transparent wrapper.
    """
    
    def __init__(self) -> None:
        self._agent: object | None = None
    
    @property
    def domain(self) -> str:
        return "stocks"
    
    def _get_agent(self) -> object | None:
        if self._agent is None:
            try:
                from src.agents.query_agent import MarketQueryAgent
                from src.agents.retriever import MarketRAGRetriever
                retriever = MarketRAGRetriever()
                self._agent = MarketQueryAgent(retriever=retriever)
            except Exception as e:
                log.warning("Stocks agent not available: {}", e)
                self._agent = False  # Sentinel — don't retry
        return self._agent if self._agent is not False else None
    
    def can_handle(self, query: str) -> tuple[bool, float]:
        q = query.lower().strip()
        if not q:
            return False, 0.0
        
        matches = sum(1 for kw in _STOCK_KEYWORDS if kw in q)
        if matches >= 3:
            return True, 0.95
        elif matches >= 1:
            return True, 0.75
        return False, 0.0
    
    def answer(self, query: str) -> str:
        agent = self._get_agent()
        if agent is None:
            return "⚠️ El mercado de acciones no está disponible en este momento (dependencias del pipeline RAG no instaladas). Probá con crypto o macroeconomía."
        return agent.run(query)
