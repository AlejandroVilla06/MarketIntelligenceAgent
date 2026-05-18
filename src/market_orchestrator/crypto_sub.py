"""CryptoSubOrchestrator — cryptocurrency data via CoinMarketCap + LLM analysis."""
from __future__ import annotations
import json
from src.market_orchestrator.sub_orchestrator import BaseSubOrchestrator
from src.utils import get_logger

log = get_logger("agents.crypto_sub")

_CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency",
    "cripto", "criptomoneda", "criptomonedas",
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
            prompt = f"""Sos un ASESOR DE INVERSIONES en criptomonedas. El usuario preguntó:

"{query}"

DATOS EN TIEMPO REAL (CoinMarketCap):
{data}

Instrucciones:
- Actuá como ASESOR FINANCIERO, no como programador
- Si el usuario pregunta "en qué invertir" o busca consejo, recomendá activos concretos (ej: BTC, ETH, SOL) con fundamento de mercado
- NUNCA generes código Python ni pidas al usuario que ejecute scripts
- Respondé en el mismo idioma de la consulta
- Analizá los datos como un analista financiero, no los listes crudos
- Incluí contexto: ¿el precio subió o bajó? ¿qué implica para un inversor?
- Mencioná fuentes: CoinMarketCap para datos en tiempo real
- Formato: narrativo, ejecutivo, sin código, en párrafos cortos"""
            
            response = llm.invoke([
                {"role": "system", "content": "Sos un asesor de inversiones en criptomonedas con datos en tiempo real de CoinMarketCap. NUNCA generás código Python. Tu objetivo es ACONSEJAR, no programar."},
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
            llm_response = self._analyze_with_llm(query, raw_data)
            
            # Build widget marker from RAW data (not LLM output)
            widget_marker = self._build_crypto_marker(raw_data, query)
            
            if widget_marker:
                return llm_response + "\n\n" + widget_marker
            return llm_response
        except Exception as e:
            log.error(f"CryptoSubOrchestrator failed: {e}")
            return f"📡 **Datos Crypto en tiempo real**\n\nError al procesar: {e}"
    
    def _build_crypto_marker(self, raw_data: str, query: str) -> str | None:
        """Build [WIDGET:crypto]{json}[/WIDGET] from raw MCP data.
        
        Extracts structured fields from the CoinMarketCap text output.
        If parsing fails, returns None (no marker, text-only fallback).
        """
        try:
            import re
            data = {}
            lines = raw_data.strip().split("\n")
            for line in lines:
                line = line.strip()
                # "CRYPTO DATA — Bitcoin (BTC)" or " 1. Bitcoin (BTC) → ..."
                if "(" in line and ")" in line and not data.get("symbol"):
                    m = re.search(r'\(([A-Z]+)\)', line)
                    if m:
                        data["symbol"] = m.group(1)
                    # Extract name: handles "— Name (" or "-- Name (" or " 1. Name  ("
                    name_m = re.search(r'[—\-]\s*(.+?)\s*\(', line)
                    if not name_m:
                        name_m = re.search(r'^\s*\d+\.\s*(.+?)\s{2,}\(', line)
                    if name_m:
                        data["name"] = name_m.group(1).strip()
                elif "Precio:" in line or "Price:" in line:
                    m = re.search(r'\$?([\d,]+\.?\d*)', line)
                    if m:
                        data["price"] = float(m.group(1).replace(",", ""))
                elif "Cambio 24h:" in line or "24h Change:" in line or "24h:" in line:
                    m = re.search(r'([+-]?\d+\.?\d*)%', line)
                    if m:
                        data["change24h"] = float(m.group(1))
                elif "Capitalización:" in line or "Capitalization:" in line or "Market Cap:" in line or "Cap:" in line:
                    m = re.search(r'\$?([\d,]+\.?\d*)', line)
                    if m:
                        data["marketCap"] = float(m.group(1).replace(",", ""))
                elif "Market cap rank:" in line or "rank:" in line or "#" in line:
                    m = re.search(r'#\s*(\d+)', line)
                    if m:
                        data["rank"] = int(m.group(1))
            
            if not data.get("symbol") or not data.get("price"):
                # Try fallback from query
                known = {"btc": "BTC", "bitcoin": "BTC", "eth": "ETH", "ethereum": "ETH",
                         "sol": "SOL", "solana": "SOL", "xrp": "XRP", "ada": "ADA",
                         "doge": "DOGE", "dot": "DOT", "avax": "AVAX", "link": "LINK"}
                q = query.lower()
                for name, sym in known.items():
                    if name in q:
                        data["symbol"] = sym
                        break
            
            if data.get("symbol") and data.get("price"):
                return f'[WIDGET:crypto]{json.dumps(data)}[/WIDGET]'
            return None
        except Exception as e:
            log.warning(f"Could not build crypto marker: {e}")
            return None
