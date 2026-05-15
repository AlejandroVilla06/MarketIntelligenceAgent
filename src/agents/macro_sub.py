"""MacroSubOrchestrator — macroeconomic data via FRED + LLM analysis."""
from __future__ import annotations
from src.agents.sub_orchestrator import BaseSubOrchestrator
from src.utils import get_logger

log = get_logger("agents.macro_sub")

_MACRO_KEYWORDS = [
    "gdp", "economy", "economic", "macro", "macroeconomics",
    "inflation", "cpi", "consumer price", "price index",
    "unemployment", "employment", "jobs", "labor", "jobless",
    "interest rate", "fed rate", "federal reserve", "fed funds",
    "treasury", "bond yield", "yield curve", "dgs10", "dgs2",
    "recession", "growth", "gross domestic product",
    "monetary policy", "fiscal policy", "stimulus",
]


class MacroSubOrchestrator(BaseSubOrchestrator):
    """Handles macroeconomic queries via FRED + LLM analysis."""

    def __init__(self) -> None:
        self._llm = None

    def _get_llm(self):
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
                log.warning(f"Could not init LLM for macro: {e}")
                self._llm = False
        return self._llm if self._llm is not False else None

    def _analyze_with_llm(self, query: str, data: str) -> str:
        """Format raw FRED data into natural language analysis."""
        llm = self._get_llm()
        if not llm:
            return data

        try:
            prompt = f"""Sos un economista senior. El usuario preguntó:

"{query}"

DATOS MACROECONÓMICOS EN TIEMPO REAL (FRED - Federal Reserve):
{data}

Instrucciones:
- Respondé en el mismo idioma de la consulta
- Analizá los datos como un economista: ¿qué implican para la economía?
- Incluí contexto histórico si es relevante
- Mencioná fuentes: FRED (Federal Reserve Economic Data)
- Formato: narrativo, ejecutivo, en párrafos cortos"""

            response = llm.invoke([
                {"role": "system", "content": "Sos un economista senior con datos macroeconómicos en tiempo real de la Reserva Federal (FRED)."},
                {"role": "user", "content": prompt},
            ])
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            log.warning(f"LLM macro analysis failed: {e}")
            return data

    @property
    def domain(self) -> str:
        return "macro"

    def can_handle(self, query: str) -> tuple[bool, float]:
        q = query.lower().strip()
        if not q:
            return False, 0.0

        matches = sum(1 for kw in _MACRO_KEYWORDS if kw in q)
        if matches >= 2:
            return True, 0.95
        elif matches >= 1:
            return True, 0.80
        return False, 0.0

    def _get_macro_data(self, query: str) -> str:
        """Lazy import and call FRED MCP functions."""
        # Lazy import — MCP package takes ~1.4s to load
        from src.agents.mcp.macro_server import (
            get_gdp, get_cpi, get_unemployment,
            get_federal_funds_rate, get_treasury_yield_10y,
            get_treasury_yield_2y, get_macro_summary,
        )
        
        q = query.lower()

        if "summary" in q or "overview" in q or "general" in q or (("economy" in q or "macro" in q) and not any(x in q for x in ["gdp", "inflation", "unemployment", "rate", "yield"])):
            return get_macro_summary()
        if "gdp" in q:
            return get_gdp()
        if "cpi" in q or "inflation" in q or "consumer price" in q:
            return get_cpi()
        if "unemployment" in q or "jobless" in q or "employment" in q:
            return get_unemployment()
        if "fed" in q or "interest" in q or "federal fund" in q:
            return get_federal_funds_rate()
        if "10-year" in q or "10y" in q or "dgs10" in q:
            return get_treasury_yield_10y()
        if "2-year" in q or "2y" in q or "dgs2" in q:
            return get_treasury_yield_2y()
        if "yield curve" in q or "treasury" in q:
            return f"{get_treasury_yield_2y()}\n{get_treasury_yield_10y()}"
        return get_macro_summary()

    def answer(self, query: str) -> str:
        try:
            raw_data = self._get_macro_data(query)
            return self._analyze_with_llm(query, raw_data)
        except Exception as e:
            log.error(f"MacroSubOrchestrator failed: {e}")
            return f"📡 **Datos Macroeconómicos en tiempo real**\n\n_FRED (Federal Reserve) consultado exitosamente._\n\nError al procesar: {e}"
