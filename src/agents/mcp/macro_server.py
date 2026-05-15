"""MCP Server: FRED macroeconomic data."""
from __future__ import annotations
import os
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("macro-economics")
FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = os.getenv("FRED_API_KEY", "")


def _fetch_series(series_id: str, name: str, limit: int = 3) -> str:
    """Fetch a FRED time series and return formatted string."""
    try:
        with httpx.Client() as client:
            resp = client.get(
                FRED_API_BASE,
                params={
                    "series_id": series_id,
                    "api_key": FRED_API_KEY,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": limit,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                observations = data.get("observations", [])
                if not observations:
                    return f"{name}: No data available"
                
                lines = [f"{name}:"]
                for obs in observations[:limit]:
                    date = obs.get("date", "")
                    value = obs.get("value", "")
                    lines.append(f"  {date}: {value}")
                return "\n".join(lines)
            return f"{name}: Error HTTP {resp.status_code}"
    except Exception as e:
        return f"{name}: Error — {e}"


@mcp.tool()
def get_gdp() -> str:
    """Get latest US GDP (Gross Domestic Product) data."""
    return _fetch_series("GDP", "US Gross Domestic Product")


@mcp.tool()
def get_cpi() -> str:
    """Get latest US CPI (Consumer Price Index / inflation) data."""
    return _fetch_series("CPIAUCSL", "US Consumer Price Index (CPI)")


@mcp.tool()
def get_unemployment() -> str:
    """Get latest US unemployment rate."""
    return _fetch_series("UNRATE", "US Unemployment Rate")


@mcp.tool()
def get_federal_funds_rate() -> str:
    """Get latest US Federal Funds effective rate (interest rate)."""
    return _fetch_series("FEDFUNDS", "Federal Funds Effective Rate")


@mcp.tool()
def get_treasury_yield_10y() -> str:
    """Get latest 10-Year US Treasury yield."""
    return _fetch_series("DGS10", "10-Year Treasury Yield")


@mcp.tool()
def get_treasury_yield_2y() -> str:
    """Get latest 2-Year US Treasury yield."""
    return _fetch_series("DGS2", "2-Year Treasury Yield")


@mcp.tool()
def get_macro_summary() -> str:
    """Get a summary of key macroeconomic indicators."""
    indicators = [
        ("GDP", "US Gross Domestic Product"),
        ("CPIAUCSL", "Consumer Price Index"),
        ("UNRATE", "Unemployment Rate"),
        ("FEDFUNDS", "Federal Funds Rate"),
        ("DGS10", "10-Year Treasury Yield"),
    ]
    
    parts = ["Macroeconomic Summary:\n"]
    for series_id, name in indicators:
        parts.append(_fetch_series(series_id, name, limit=1))
        parts.append("")
    
    return "\n".join(parts)


if __name__ == "__main__":
    mcp.run()
