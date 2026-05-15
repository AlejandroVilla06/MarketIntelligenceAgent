"""MCP Server: CoinMarketCap cryptocurrency data."""
from __future__ import annotations
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("crypto-market")
CMC_API_BASE = "https://pro-api.coinmarketcap.com/v1"


def _get_api_key() -> str:
    """Lazy-load API key from settings (not os.getenv)."""
    from src.config import settings
    return settings.coinmarketcap_api_key


def _get_headers() -> dict:
    key = _get_api_key()
    if not key:
        return {}
    return {"X-CMC_PRO_API_KEY": key}


@mcp.tool()
def get_crypto_price(symbol: str) -> str:
    """Get current price and market data for a cryptocurrency.
    
    Args:
        symbol: Coin symbol (BTC, ETH, SOL, etc.)
    """
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ CoinMarketCap API key no configurada. Configurá COINMARKETCAP_API_KEY en el .env"
    
    try:
        with httpx.Client() as client:
            resp = client.get(
                f"{CMC_API_BASE}/cryptocurrency/quotes/latest",
                headers={"X-CMC_PRO_API_KEY": api_key},
                params={"symbol": symbol.upper(), "convert": "USD"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()["data"]
                coin = data.get(symbol.upper(), {})
                quote = coin.get("quote", {}).get("USD", {})
                return (
                    f"CRYPTO DATA — {coin.get('name', symbol.upper())} ({symbol.upper()})\n"
                    f"Precio: ${quote.get('price', 0):,.2f} USD\n"
                    f"Capitalización: ${quote.get('market_cap', 0):,.0f}\n"
                    f"Volumen 24h: ${quote.get('volume_24h', 0):,.0f}\n"
                    f"Cambio 24h: {quote.get('percent_change_24h', 0):+.2f}%\n"
                    f"Cambio 7d: {quote.get('percent_change_7d', 0):+.2f}%\n"
                    f"Supply circulante: {coin.get('circulating_supply', 0):,.0f}\n"
                    f"Market cap rank: #{coin.get('cmc_rank', 'N/A')}\n"
                    f"Fuente: CoinMarketCap (tiempo real)"
                )
            elif resp.status_code == 401:
                return f"⚠️ CoinMarketCap: API key inválida. Verificá COINMARKETCAP_API_KEY"
            else:
                return f"CoinMarketCap: HTTP {resp.status_code}"
    except httpx.TimeoutException:
        return "⚠️ CoinMarketCap: timeout de conexión"
    except Exception as e:
        return f"CoinMarketCap error: {e}"


@mcp.tool()
def get_top_cryptos(limit: int = 10) -> str:
    """Get top cryptocurrencies by market cap.
    
    Args:
        limit: Number of coins to return (max 100)
    """
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ CoinMarketCap API key no configurada"
    
    try:
        with httpx.Client() as client:
            resp = client.get(
                f"{CMC_API_BASE}/cryptocurrency/listings/latest",
                headers={"X-CMC_PRO_API_KEY": api_key},
                params={"limit": min(limit, 100), "convert": "USD"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()["data"]
                lines = ["TOP CRYPTO — Ranking por capitalización de mercado:\n"]
                for i, coin in enumerate(data[:limit], 1):
                    quote = coin.get("quote", {}).get("USD", {})
                    lines.append(
                        f"{i:2d}. {coin['name']:20s} ({coin['symbol']:6s}) → "
                        f"${quote.get('price', 0):>10,.2f} | "
                        f"Cap: ${quote.get('market_cap', 0):>12,.0f} | "
                        f"24h: {quote.get('percent_change_24h', 0):+7.2f}%"
                    )
                lines.append("\nFuente: CoinMarketCap (tiempo real)")
                return "\n".join(lines)
            return f"CoinMarketCap error: HTTP {resp.status_code}"
    except httpx.TimeoutException:
        return "⚠️ CoinMarketCap: timeout de conexión"
    except Exception as e:
        return f"CoinMarketCap error: {e}"


@mcp.tool()
def get_crypto_global_metrics() -> str:
    """Get global cryptocurrency market metrics."""
    api_key = _get_api_key()
    if not api_key:
        return "⚠️ CoinMarketCap API key no configurada"
    
    try:
        with httpx.Client() as client:
            resp = client.get(
                f"{CMC_API_BASE}/global-metrics/quotes/latest",
                headers={"X-CMC_PRO_API_KEY": api_key},
                params={"convert": "USD"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()["data"]
                quote = data.get("quote", {}).get("USD", {})
                return (
                    f"CRYPTO GLOBAL — Métricas del mercado:\n"
                    f"Capitalización total: ${quote.get('total_market_cap', 0):,.0f}\n"
                    f"Volumen 24h total: ${quote.get('total_volume_24h', 0):,.0f}\n"
                    f"Dominancia BTC: {data.get('btc_dominance', 0):.1f}%\n"
                    f"Dominancia ETH: {data.get('eth_dominance', 0):.1f}%\n"
                    f"Criptos activas: {data.get('active_cryptocurrencies', 0)}\n"
                    f"Mercados: {data.get('active_market_pairs', 0)}\n"
                    f"Cambio cap total 24h: {quote.get('total_market_cap_yesterday_percent_change', 0):+.2f}%\n"
                    f"Fuente: CoinMarketCap (tiempo real)"
                )
            return f"CoinMarketCap error: HTTP {resp.status_code}"
    except httpx.TimeoutException:
        return "⚠️ CoinMarketCap: timeout de conexión"
    except Exception as e:
        return f"CoinMarketCap error: {e}"
