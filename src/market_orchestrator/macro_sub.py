"""MacroSubOrchestrator — macroeconomic data via FRED + LLM analysis."""
from __future__ import annotations
import json
from src.market_orchestrator.sub_orchestrator import BaseSubOrchestrator
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
        """Lazy-init LLM — uses shared singleton from llm_provider."""
        if self._llm is None:
            from src.market_orchestrator.llm_provider import get_llm
            self._llm = get_llm() or False
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

Respondé natural, sin estructura fija. Analizá los datos como un economista: ¿qué implican para la economía? Incluí contexto histórico si es relevante. Mencioná FRED (Federal Reserve Economic Data) como fuente. Respondé en el mismo idioma de la consulta. Usá un tono narrativo, como si estuvieras explicando la situación económica a un cliente."""

            response = llm.invoke([
                {"role": "system", "content": "Sos un economista senior con datos macroeconómicos en tiempo real de la Reserva Federal (FRED). Respondé de forma natural, sin plantillas fijas."},
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
            llm_response = self._analyze_with_llm(query, raw_data)
            widget_marker = self._build_macro_marker(raw_data)
            if widget_marker:
                return llm_response + "\n\n" + widget_marker
            return llm_response
        except Exception as e:
            log.error(f"MacroSubOrchestrator failed: {e}")
            return f"📡 **Datos Macroeconómicos en tiempo real**\n\nError al procesar: {e}"
    
    def _build_macro_marker(self, raw_data: str) -> str | None:
        """Build [WIDGET:macro]{json}[/WIDGET] from raw FRED data."""
        try:
            import re
            data = {}
            lines = raw_data.strip().split("\n")
            for line in lines:
                if ":" in line:
                    parts = line.split(":", 1)
                    key = parts[0].strip()
                    val = parts[1].strip() if len(parts) > 1 else ""
                    
                    if "GDP" in key or "Gross Domestic Product" in key:
                        data["indicator"] = "GDP"
                    elif "CPI" in key or "Consumer Price" in key:
                        data["indicator"] = "CPI"
                    elif "Unemployment" in key or "UNRATE" in key:
                        data["indicator"] = "Unemployment Rate"
                    elif "Federal Funds" in key or "FEDFUNDS" in key:
                        data["indicator"] = "Federal Funds Rate"
                    else:
                        indicator_match = re.search(r'(GDP|CPI|Unemployment|Federal Funds|Treasury|10-Year|2-Year)', key)
                        if indicator_match:
                            data["indicator"] = indicator_match.group(1)
                    
                    # Try to extract value and date (date can be in key or value)
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', val)
                    if date_match:
                        data["date"] = date_match.group(1)
                    if not data.get("date"):
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', key)
                        if date_match:
                            data["date"] = date_match.group(1)
                    num_match = re.search(r'(-?\d+\.?\d*)', val)
                    if num_match:
                        data["value"] = float(num_match.group(1))
            
            # Try the FRED series name from the first line
            first_line = lines[0] if lines else ""
            if not data.get("indicator"):
                name_parts = first_line.split(":")
                data["indicator"] = name_parts[0].strip() if name_parts else "Macro Indicator"
            
            # Determine unit based on indicator
            if "GDP" in data.get("indicator", ""):
                data["unit"] = "Billions $"
            elif "CPI" in data.get("indicator", ""):
                data["unit"] = "Index"
            elif "Rate" in data.get("indicator", ""):
                data["unit"] = "%"
            elif "Yield" in data.get("indicator", ""):
                data["unit"] = "%"
            else:
                data["unit"] = ""
            
            if data.get("indicator") and data.get("value") is not None:
                return f'[WIDGET:macro]{json.dumps(data)}[/WIDGET]'
            return None
        except Exception as e:
            log.warning(f"Could not build macro marker: {e}")
            return None
