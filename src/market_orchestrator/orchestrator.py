"""
Orchestrator — Hierarchical Multi-Market Orchestrator
=====================================================

Routes queries to domain-specific sub-orchestrators via RouterAgent.
Supports: stocks, crypto, macroeconomics, financial calculations.

Usage:
    from src.market_orchestrator.orchestrator import MarketOrchestrator
    orchestrator = MarketOrchestrator()
    orchestrator.setup()
    answer = orchestrator.ask("How is Bitcoin doing?")
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.market_orchestrator.router_agent import RouterAgent
from src.market_orchestrator.stocks_sub import StocksSubOrchestrator
from src.market_orchestrator.crypto_sub import CryptoSubOrchestrator
from src.market_orchestrator.macro_sub import MacroSubOrchestrator
from src.market_orchestrator.python_repl import CalculationExecutor
from src.agents.query_agent import MarketQueryAgent
from src.agents.retriever import MarketRAGRetriever
from src.data_engine.storage import StorageInterface
from src.utils import get_logger

if TYPE_CHECKING:
    pass

log = get_logger("agents.orchestrator")


class MarketOrchestrator:
    """Hierarchical multi-market orchestrator.

    Uses RouterAgent to classify queries and delegate to the appropriate
    sub-orchestrator. Maintains backward compatibility with the original
    ask() interface.

    Args:
        persist_directory: (legacy, unused in hierarchical mode)
        model_name: (legacy, unused in hierarchical mode)
    """

    def __init__(
        self,
        persist_directory: str | None = None,
        model_name: str | None = None,
    ) -> None:
        self._is_setup = False
        self.router = RouterAgent()
        self._stocks_sub: StocksSubOrchestrator | None = None
        self._agent: MarketQueryAgent | None = None
        self._retriever: MarketRAGRetriever | None = None
        self._storage: StorageInterface | None = None

        # Legacy attrs — kept for backward compatibility with existing consumers
        self.persist_directory = persist_directory
        self.model_name = model_name
        self.retriever: MarketRAGRetriever | None = None
        self.agent: MarketQueryAgent | None = None
        self.storage: StorageInterface | None = None

    def setup(self, storage: StorageInterface | None = None) -> None:
        """Initialize all sub-orchestrators and data pipeline.

        Creates and registers the stocks, crypto, macro, and calculation
        sub-orchestrators. Also initializes the retriever and storage
        for backward compatibility.

        Args:
            storage: StorageInterface instance (creates new if None)
        """
        log.info("Setting up hierarchical MarketOrchestrator...")

        # ── Pre-calentamiento de imports pesados ──────────────────────
        # Forzar langchain_openai (~8s) en startup, no en primer request
        try:
            from src.market_orchestrator.llm_provider import warmup_llm
            warmup_llm()
        except Exception:
            pass

        self._storage = storage or StorageInterface()
        self.storage = self._storage
        # MarketRAGRetriever requiere sentence_transformers (torch ~800MB)
        # Si no está instalado, el orquestador igual funciona para crypto, macro y cálculo
        try:
            self._retriever = MarketRAGRetriever(
                persist_directory=self.persist_directory
            )
            self.retriever = self._retriever
        except Exception as e:
            log.warning("MarketRAGRetriever no disponible (stocks RAG desactivado): {}", e)
            self._retriever = None
            self.retriever = None

        # Register sub-orchestrators
        self._stocks_sub = StocksSubOrchestrator()
        self.router.register(self._stocks_sub)
        self.router.register(CryptoSubOrchestrator())
        self.router.register(MacroSubOrchestrator())
        self.router.register(CalculationExecutor())

        # MCP Health Check — no bloqueante (dispara en background)
        import threading
        threading.Thread(target=self._check_mcp_connectivity, daemon=True).start()

        self._is_setup = True
        log.info("✅ Hierarchical MarketOrchestrator setup complete")
    
    def _check_mcp_connectivity(self) -> None:
        """Test connectivity to external data providers (CoinMarketCap, FRED)."""
        from src.config import settings
        
        cmc_ok = bool(settings.coinmarketcap_api_key)
        fred_ok = bool(settings.fred_api_key)
        
        if cmc_ok:
            # Quick test: fetch BTC price
            try:
                from src.agents.mcp.crypto_server import get_crypto_price
                result = get_crypto_price("BTC")
                if "error" not in result.lower() and "⚠️" not in result:
                    log.info("✅ MCP READY — CoinMarketCap conectado y respondiendo")
                    log.info(f"   BTC: {result.split(chr(10))[1] if chr(10) in result else 'OK'}")
                else:
                    log.warning(f"⚠️ MCP CoinMarketCap conectado pero devolvió: {result[:80]}")
            except Exception as e:
                log.warning(f"⚠️ MCP CoinMarketCap: {e}")
        else:
            log.warning("⚠️ MCP CoinMarketCap: API key no configurada")
        
        if fred_ok:
            try:
                from src.agents.mcp.macro_server import get_gdp
                result = get_gdp()
                if "error" not in result.lower() and "Error" not in result:
                    log.info("✅ MCP READY — FRED conectado y respondiendo")
                    log.info(f"   GDP: {result.split(chr(10))[1] if chr(10) in result else 'OK'}")
                else:
                    log.warning(f"⚠️ MCP FRED conectado pero devolvió: {result[:80]}")
            except Exception as e:
                log.warning(f"⚠️ MCP FRED: {e}")
        else:
            log.warning("⚠️ MCP FRED: API key no configurada")

    def ask(self, query: str, history: list[dict] | None = None) -> str:
        """Ask a question — routes to the appropriate sub-orchestrator.

        If history is provided, it's passed to the stocks sub-orchestrator
        (the only one with conversation memory). Other sub-orchestrators
        are stateless.

        Args:
            query: User's question
            history: Optional conversation history (for stocks only)

        Returns:
            Analysis/response string
        """
        if not self._is_setup:
            self.setup()

        try:
            return self.router.answer(query)
        except Exception as e:
            log.error(f"Orchestrator failed: {e}")
            return f"I encountered an error: {e}"

    async def ask_stream(self, query: str, history: list[dict] | None = None):
        """Async generator for streaming responses.

        Currently only stocks supports streaming. Falls back to full response
        for other domains by splitting into word tokens.

        Args:
            query: User's question
            history: Optional conversation history

        Yields:
            str: tokens from the response
        """
        if not self._is_setup:
            self.setup()

        result = self.ask(query, history)
        # Split into words for streaming effect
        words = result.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield token

    def reset(self) -> None:
        """Reset the orchestrator (clear state and re-index on next call).

        Use this to force re-initialization of sub-orchestrators.
        """
        log.info("Resetting MarketOrchestrator...")
        self._is_setup = False
        log.info("Reset complete")

    def get_status(self) -> dict:
        """Get status of the orchestrator.

        Returns:
            Dict with component status including registered sub-orchestrators
            and legacy fields for backward compatibility.
        """
        status: dict = {
            "is_setup": self._is_setup,
            "sub_orchestrators": [
                sub.domain for sub in self.router.sub_orchestrators
            ],
            "retriever_initialized": self.retriever is not None,
            "agent_initialized": self.agent is not None,
        }

        if self.retriever is not None and self._is_setup:
            try:
                status["counts"] = self.retriever.get_counts()
            except Exception:
                status["counts"] = {}

        return status


__all__ = [
    "MarketOrchestrator",
]
