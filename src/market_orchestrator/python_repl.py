"""CalculationExecutor — financial calculations via Python REPL MCP."""
from __future__ import annotations
import asyncio
import json

from src.market_orchestrator.sub_orchestrator import BaseSubOrchestrator
from src.agents.mcp.repl_server import calculate_python
from src.utils import get_logger

log = get_logger("agents.python_repl")

_CALC_KEYWORDS = [
    # English
    "calculate", "calculation", "compute", "formula",
    "npv", "net present value", "irr", "internal rate",
    "sharpe", "value at risk",
    "beta", "alpha", "standard deviation", "volatility",
    "correlation", "covariance", "regression",
    "moving average", "sma", "ema",
    "what if",
    # Spanish — word-bounded to avoid false positives
    " cálculo", " calcular", " fórmula",
    " tir ", " tir.", " van ", " npv ",
]


class CalculationExecutor(BaseSubOrchestrator):
    """Handles financial calculations via safe Python REPL."""

    @property
    def domain(self) -> str:
        return "calculation"

    def can_handle(self, query: str) -> tuple[bool, float]:
        q = query.lower().strip()
        if not q:
            return False, 0.0

        # Use word-boundary matching for short keywords (avoid false positives)
        # and simple substring for multi-word English terms
        matches = 0
        for kw in _CALC_KEYWORDS:
            if kw in q:
                # Already space-padded for word boundary
                matches += 1
            elif len(kw) <= 4 and kw.isalpha():
                # Short alpha words: require word boundary via regex
                import re
                if re.search(rf"\b{kw}\b", q):
                    matches += 1

        if matches >= 2:
            return True, 0.95
        elif matches >= 1:
            return True, 0.75
        return False, 0.0

    def answer(self, query: str) -> str:
        q = query.lower()

        try:
            # Map natural language queries to code templates
            if "npv" in q or "net present value" in q:
                result = self._calculate_npv(q)
            elif "irr" in q or "internal rate" in q:
                result = "IRR requiere cálculo iterativo. Usá: calculate_python con el código apropiado."
            elif "sharpe" in q:
                result = self._calculate_sharpe()
            elif "moving average" in q or "sma" in q:
                result = self._calculate_sma()
            else:
                result = "Decime exactamente qué querés calcular (NPV, Sharpe, etc.) y te ayudo con el código Python."
            
            # Build calc widget marker from query and result
            widget_marker = self._build_calc_marker(query, result)
            if widget_marker:
                return result + "\n\n" + widget_marker
            return result
        except Exception as e:
            log.error(f"CalculationExecutor failed: {e}")
            return f"Error en el cálculo: {e}"
    
    def _build_calc_marker(self, query: str, result_text: str) -> str | None:
        """Build [WIDGET:calc]{json}[/WIDGET] from calculation result."""
        try:
            import re
            data = {"formula": "Calculation"}
            q = query.lower()
            if "npv" in q:
                data["formula"] = "NPV"
            elif "sharpe" in q:
                data["formula"] = "Sharpe Ratio"
            elif "sma" in q or "moving average" in q:
                data["formula"] = "SMA"
            
            # Try to extract result value from the output text
            for line in result_text.split("\n"):
                if "NPV:" in line or "Sharpe" in line or "NPV" in line:
                    num_m = re.search(r'(-?\d+\.?\d*)', line)
                    if num_m:
                        data["result"] = float(num_m.group(1))
                        break
            
            if "result" not in data:
                data["result"] = "See analysis above"
            
            # Interpretation based on formula and result
            if isinstance(data.get("result"), (int, float)):
                if data["formula"] == "NPV":
                    data["interpretation"] = "Positive NPV: Project adds value ✅" if data["result"] > 0 else "Negative NPV: Project destroys value ❌"
                elif data["formula"] == "Sharpe Ratio":
                    if data["result"] > 2:
                        data["interpretation"] = "Excellent risk-adjusted return"
                    elif data["result"] > 1:
                        data["interpretation"] = "Good risk-adjusted return"
                    else:
                        data["interpretation"] = "Average or poor risk-adjusted return"
            
            return f'[WIDGET:calc]{json.dumps(data)}[/WIDGET]'
        except Exception as e:
            log.warning(f"Could not build calc marker: {e}")
            return None

    def _calculate_npv(self, query: str) -> str:
        """Calculate NPV based on query context."""
        code = """# Net Present Value example
# Cash flows: $100 yearly for 5 years, discount rate 10%
cash_flows = [100, 100, 100, 100, 100]
rate = 0.10

npv = sum([cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows)])
initial = 400  # Initial investment

print(f"Present value of cash flows: ${npv:,.2f}")
print(f"Initial investment: ${initial:,.2f}")
print(f"NPV: ${npv - initial:,.2f}")
if npv > initial:
    print("=> Positive NPV: Project adds value ✅")
else:
    print("=> Negative NPV: Project destroys value ❌")
"""
        result = calculate_python(code)
        return f"## NPV Calculation\n\n{result}\n\n💡 *Podés ajustar los valores editando cash_flows, rate e initial*"

    def _calculate_sharpe(self) -> str:
        code = """# Sharpe Ratio calculation
import numpy as np

# Example daily returns (decimal form)
daily_returns = [0.01, -0.005, 0.02, 0.015, -0.01, 0.008, 0.012, -0.003, 0.018, 0.005]

mean_return = np.mean(daily_returns)
std_dev = np.std(daily_returns, ddof=1)
risk_free_rate = 0.05  # 5% annual

# Annualized Sharpe (252 trading days)
sharpe = (mean_return * 252 - risk_free_rate) / (std_dev * np.sqrt(252))

print(f"Mean daily return: {mean_return*100:.2f}%")
print(f"Daily std dev: {std_dev*100:.2f}%")
print(f"Annualized Sharpe Ratio: {sharpe:.2f}")
if sharpe > 2:
    print("Rating: Excellent ⭐⭐⭐⭐⭐")
elif sharpe > 1:
    print("Rating: Good ⭐⭐⭐⭐")
elif sharpe > 0:
    print("Rating: Average ⭐⭐⭐")
else:
    print("Rating: Poor ⭐⭐")
"""
        return f"## Sharpe Ratio Calculation\n\n{calculate_python(code)}"

    def _calculate_sma(self) -> str:
        code = """# Simple Moving Average (SMA)
import pandas as pd

# Example price data
prices = [100, 102, 101, 105, 107, 106, 108, 110, 109, 111,
          113, 112, 115, 114, 116, 118, 117, 119, 120, 121]

sma_5 = pd.Series(prices).rolling(window=5).mean()
sma_10 = pd.Series(prices).rolling(window=10).mean()

print(f"Prices (last 5): {prices[-5:]}")
print(f"SMA-5 (last 5): {[round(x, 2) for x in sma_5.dropna().tolist()[-5:]]}")
print(f"SMA-10 (last 5): {[round(x, 2) for x in sma_10.dropna().tolist()[-5:]]}")
print(f"Current price: ${prices[-1]}")
print(f"SMA-5: ${sma_5.iloc[-1]:.2f}")
print(f"SMA-10: ${sma_10.iloc[-1]:.2f}")
if prices[-1] > sma_5.iloc[-1]:
    print("=> Price above SMA-5: Short-term bullish 📈")
else:
    print("=> Price below SMA-5: Short-term bearish 📉")
"""
        return f"## Simple Moving Average (SMA)\n\n{calculate_python(code)}"

    async def get_recent_history(self, user_id: str, limit: int = 10) -> str:
        """Get recent conversation history for cross-session calculations.

        Retrieves the last N conversations for the user, formatted as context
        for the LLM. Filtered by user_id for isolation.

        Args:
            user_id: The authenticated user's UUID
            limit: Max conversations to retrieve

        Returns:
            Formatted string with recent conversation history, or empty string
        """
        try:
            from src.api.auth.supabase_client import get_supabase_client

            supabase = get_supabase_client()

            result = await asyncio.to_thread(
                supabase.table("conversations")
                    .select("id, title")
                    .eq("user_id", user_id)
                    .order("updated_at", desc=True)
                    .limit(limit)
                    .execute
            )

            if not result.data:
                return ""

            history_parts = ["📋 Recent conversation history:\n"]

            for conv in result.data:
                messages = await asyncio.to_thread(
                    supabase.table("messages")
                        .select("role, content")
                        .eq("conversation_id", conv["id"])
                        .order("created_at")
                        .execute
                )

                if messages.data:
                    history_parts.append(f"\n## {conv['title']}")
                    for msg in messages.data[-6:]:  # Last 6 messages per conversation
                        prefix = "👤" if msg["role"] == "user" else "🤖"
                        content = msg["content"][:200]  # Truncate long messages
                        history_parts.append(f"{prefix} {content}")

            return "\n".join(history_parts)
        except Exception as e:
            log.warning(f"Could not retrieve history: {e}")
            return ""
