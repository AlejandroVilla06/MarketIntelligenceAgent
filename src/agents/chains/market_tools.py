"""
Market Tools - LangChain @tool Wrappers for RAG Retriever
=======================================================

LangChain tool definitions wrapping MarketRAGRetriever methods.
Provides function-calling interface for ReAct agent.

Usage:
    from src.agents.chains.market_tools import get_retriever_tools
    tools = get_retriever_tools()
"""

from __future__ import annotations

from langchain_core.tools import tool

from src.config import settings


# =============================================================================
# LATENCY TRACKING WRAPPER
# =============================================================================

def _track_operation(operation: str, func: callable) -> callable:
    """Wrapper to track latency of a function call."""
    from src.agents.cache import get_latency_tracker
    tracker = get_latency_tracker()
    tracker.start(operation)
    try:
        result = func()
        tracker.finish(operation, success=True)
        return result
    except Exception as e:
        tracker.finish(operation, success=False, error=str(e))
        raise


@tool
def query_stocks_tool(
    query: str,
    k: int | None = None,
) -> list[dict]:
    """
    Query stock market data for symbol, price, volume, and technical indicators.

    Args:
        query: Search query (e.g., "AAPL stock data", "NVDA price trend")
        k: Number of results (default: 5)

    Returns:
        List of stock data records with document, metadata, distance
    """
    from src.agents.retriever import MarketRAGRetriever

    def _execute():
        retriever = MarketRAGRetriever()
        k = k or settings.rag_default_k
        return retriever.query_stocks(query, k)

    return _track_operation("query_stocks", _execute)


@tool
def query_news_tool(
    query: str,
    k: int | None = None,
) -> list[dict]:
    """
    Query financial news articles.

    Args:
        query: Search query (e.g., "AAPL earnings", "tech sector news")
        k: Number of results (default: 5)

    Returns:
        List of news records with document, metadata, distance
    """
    from src.agents.retriever import MarketRAGRetriever

    def _execute():
        retriever = MarketRAGRetriever()
        k = k or settings.rag_default_k
        return retriever.query_news(query, k)

    return _track_operation("query_news", _execute)


@tool
def query_sentiment_tool(
    query: str,
    k: int | None = None,
) -> list[dict]:
    """
    Query market sentiment data for symbols.

    Args:
        query: Search query (e.g., "AAPL sentiment", "NVDA investor mood")
        k: Number of results (default: 5)

    Returns:
        List of sentiment records with document, metadata, distance
    """
    from src.agents.retriever import MarketRAGRetriever

    def _execute():
        retriever = MarketRAGRetriever()
        k = k or settings.rag_default_k
        return retriever.query_sentiment(query, k)

    return _track_operation("query_sentiment", _execute)


@tool
def query_all_tool(
    query: str,
    k_per_collection: int | None = None,
) -> dict[str, list[dict]]:
    """
    Query all market data collections (stocks, news, sentiment).

    Use this for comprehensive queries that need multiple data types.
    Example: "How did AAPL news affect stock price last week?"

    Args:
        query: Search query
        k_per_collection: Results per collection (default: 5)

    Returns:
        Dict with keys: stocks, news, sentiment
    """
    from src.agents.retriever import MarketRAGRetriever

    def _execute():
        retriever = MarketRAGRetriever()
        k = k_per_collection or settings.rag_default_k
        return retriever.query_all(query, k)

    # Try cache first (if enabled in settings)
    import json
    cache_result = None

    try:
        if getattr(settings, 'cache_enabled', False):
            from src.agents.cache import get_cache_instance
            cache = get_cache_instance()
            # Cache key includes query + operation type
            cache_result = cache.get(query, model_id="query_all")
            if cache_result:
                # Cache hit - return cached result
                return json.loads(cache_result)
    except Exception:
        # Cache errors should not break the tool
        pass

    # Cache miss - execute and store
    result = _track_operation("query_all", _execute)

    try:
        if getattr(settings, 'cache_enabled', False) and cache_result is None:
            from src.agents.cache import get_cache_instance
            cache = get_cache_instance()
            cache.set(query, json.dumps(result), model_id="query_all")
    except Exception:
        # Cache errors should not break the tool
        pass

    return result


# =============================================================================
# PHASE 2: CORRELATION TOOLS — Sprint 4
# =============================================================================


@tool
def get_sentiment_price_correlation_tool(
    symbol: str,
    window_days: int = 30,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    Compute statistical correlation between Llama 3.1 sentiment and stock price.

    Call this when the user asks about the relationship between sentiment and price,
    e.g., "How did sentiment correlate with AAPL price?",
    "Is AAPL sentiment bullish when price rises?".

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "NVDA")
        window_days: Number of days to analyze (default: 30)
        start_date: Start date YYYY-MM-DD (optional, defaults to window_days ago)
        end_date: End date YYYY-MM-DD (optional, defaults to today)

    Returns:
        JSON string with correlation metrics or status error.
    """
    import json
    from datetime import date, timedelta
    from src.agents.retriever import MarketRAGRetriever
    from scipy.stats import spearmanr
    import polars as pl

    retriever = MarketRAGRetriever()

    # Resolve date range
    end = end_date or date.today().isoformat()
    start = start_date or (date.today() - timedelta(days=window_days)).isoformat()

    # Layer 1: fetch from retriever
    sentiment_data = retriever.query_by_metadata(
        collection="sentiment",
        query="",
        symbol=symbol,
        start_date=start,
        end_date=end,
    )
    stock_data = retriever.query_by_metadata(
        collection="stocks",
        query="",
        symbol=symbol,
        start_date=start,
        end_date=end,
    )

    # Layer 2: validate overlap
    sentiment_dates = {r["metadata"].get("date") for r in sentiment_data}
    stock_dates = {r["metadata"].get("date") for r in stock_data}
    overlap = sentiment_dates & stock_dates

    if len(overlap) < 10:
        result = {
            "status": "insufficient_data",
            "overlap_count": len(overlap),
            "min_required": 10,
            "available_sentiment_range": [
                min(sentiment_dates) if sentiment_dates else None,
                max(sentiment_dates) if sentiment_dates else None,
            ],
            "available_stock_range": [
                min(stock_dates) if stock_dates else None,
                max(stock_dates) if stock_dates else None,
            ],
        }
        return json.dumps(result)

    if not overlap:
        result = {
            "status": "no_overlap",
            "available_sentiment_range": [
                min(sentiment_dates) if sentiment_dates else None,
                max(sentiment_dates) if sentiment_dates else None,
            ],
            "available_stock_range": [
                min(stock_dates) if stock_dates else None,
                max(stock_dates) if stock_dates else None,
            ],
            "warning": (
                f"Only {len(overlap)} overlapping days found. "
                "Results may not be statistically significant."
            ),
        }
        return json.dumps(result)

    # Build Polars DataFrames
    s_rows = [
        {"date": r["metadata"].get("date"), "sentiment_score": r["metadata"].get("sentiment_score", 0.0)}
        for r in sentiment_data
    ]
    p_rows = [
        {"date": r["metadata"].get("date"), "close": r["metadata"].get("close", 0.0)}
        for r in stock_data
    ]

    df_aligned = pl.DataFrame(s_rows).join(
        pl.DataFrame(p_rows), on="date", how="inner"
    ).sort("date")

    # Compute price change percentage
    df_aligned = df_aligned.with_columns(
        (pl.col("close").pct_change().fill_null(0.0) * 100).alias("price_change_pct")
    )

    # Pearson: Polars
    pearson = float(df_aligned["sentiment_score"].corr(df_aligned["price_change_pct"]))

    # Spearman: scipy
    spearman_ = float(spearmanr(
        df_aligned["sentiment_score"].to_numpy(),
        df_aligned["price_change_pct"].to_numpy(),
    )[0])

    # Direction labels
    avg_sentiment = float(df_aligned["sentiment_score"].mean())
    avg_change = float(df_aligned["price_change_pct"].mean())
    price_direction = "up" if avg_change > 0.5 else "down" if avg_change < -0.5 else "flat"
    sentiment_direction = "positive" if avg_sentiment > 0.1 else "negative" if avg_sentiment < -0.1 else "neutral"

    # Daily breakdown
    daily_breakdown = [
        {"date": row["date"], "sentiment_score": round(row["sentiment_score"], 3),
         "close": row["close"], "price_change_pct": round(row["price_change_pct"], 3)}
        for row in df_aligned.to_dicts()
    ]

    result = {
        "status": "success",
        "pearson_coefficient": round(pearson, 3),
        "spearman_coefficient": round(spearman_, 3),
        "sentiment_direction": sentiment_direction,
        "price_direction": price_direction,
        "overlap_actual_days": len(overlap),
        "daily_breakdown": daily_breakdown,
        "sentiment_range": [start, end],
        "stock_range": [start, end],
    }

    if len(overlap) < 15:
        result["warning"] = f"Small sample ({len(overlap)} days) — interpret with caution."

    return json.dumps(result)


@tool
def align_by_temporal_window_tool(
    symbol: str,
    start: str,
    end: str,
    lookback_days: int = 0,
) -> str:
    """
    Align sentiment and stock data into a single DataFrame by symbol and date range.

    Call this when the user asks for aligned time series data or a table with both
    sentiment and price on the same dates, e.g., "Show me AAPL's data for January",
    "Align sentiment and price for TSLA this week".

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "NVDA")
        start: Start date YYYY-MM-DD
        end: End date YYYY-MM-DD
        lookback_days: Include N days before start for computing price change (default: 0)

    Returns:
        JSON string with aligned DataFrame or status error.
    """
    import json
    from datetime import date, timedelta
    from src.agents.retriever import MarketRAGRetriever
    import polars as pl

    retriever = MarketRAGRetriever()

    # Validate date order
    if end < start:
        raise ValueError(f"end_date '{end}' cannot be before start_date '{start}'")

    # Extend range for lookback
    actual_start = (date.fromisoformat(start) - timedelta(days=lookback_days)).isoformat()

    # Fetch both collections
    sentiment_data = retriever.query_by_metadata(
        collection="sentiment", query="", symbol=symbol,
        start_date=actual_start, end_date=end,
    )
    stock_data = retriever.query_by_metadata(
        collection="stocks", query="", symbol=symbol,
        start_date=actual_start, end_date=end,
    )

    # Check overlap
    sentiment_dates = {r["metadata"].get("date") for r in sentiment_data}
    stock_dates = {r["metadata"].get("date") for r in stock_data}
    overlap_dates = sorted(sentiment_dates & stock_dates)

    if not overlap_dates:
        result = {
            "status": "no_overlap",
            "available_sentiment_range": [
                min(sentiment_dates), max(sentiment_dates)
            ] if sentiment_dates else [None, None],
            "available_stock_range": [
                min(stock_dates), max(stock_dates)
            ] if stock_dates else [None, None],
        }
        return json.dumps(result)

    # Build aligned DataFrame
    s_rows = [
        {"date": r["metadata"].get("date"),
         "sentiment_score": r["metadata"].get("sentiment_score", 0.0),
         "sentiment_label": r["metadata"].get("sentiment_label", "neutral")}
        for r in sentiment_data
    ]
    p_rows = [
        {"date": r["metadata"].get("date"),
         "close": r["metadata"].get("close", 0.0),
         "volume": r["metadata"].get("volume", 0)}
        for r in stock_data
    ]

    df_aligned = pl.DataFrame(s_rows).join(
        pl.DataFrame(p_rows), on="date", how="inner"
    ).sort("date")

    # Compute price change
    df_aligned = df_aligned.with_columns(
        (pl.col("close").pct_change().fill_null(0.0) * 100).alias("price_change_pct"),
        pl.when(pl.col("close").pct_change().fill_null(0.0) > 0.005).then(pl.lit("up"))
        .when(pl.col("close").pct_change().fill_null(0.0) < -0.005).then(pl.lit("down"))
        .otherwise(pl.lit("flat")).alias("price_change_direction"),
    )

    # Filter to original range (exclude lookback from output)
    df_out = df_aligned.filter(pl.col("date") >= start)

    aligned_rows = [
        {"date": row["date"], "symbol": symbol,
         "sentiment_score": row["sentiment_score"],
         "sentiment_label": row["sentiment_label"],
         "price_close": row["close"],
         "price_volume": row["volume"],
         "price_change_pct": round(row["price_change_pct"], 3),
         "price_change_direction": row["price_change_direction"]}
        for row in df_out.to_dicts()
    ]

    # Missing sentiment dates (cap at 20)
    all_dates_in_range = [d for d in sorted(sentiment_dates | stock_dates) if start <= d <= end]
    missing_ = [d for d in all_dates_in_range if d not in overlap_dates][:20]

    result = {
        "status": "success",
        "aligned_rows": aligned_rows,
        "validation_metadata": {
            "sentiment_available": [min(sentiment_dates), max(sentiment_dates)],
            "stock_available": [min(stock_dates), max(stock_dates)],
            "requested": [start, end],
            "aligned": [start, end] if aligned_rows else [None, None],
            "overlap_valid": len(overlap_dates) > 0,
        },
        "overlap_count": len(overlap_dates),
    }

    if missing_:
        result["missing_sentiment_dates"] = missing_
        result["warning"] = f"Sentiment data missing for {len(missing_)} date(s)"

    return json.dumps(result)


@tool
def get_cross_collection_context_tool(
    symbol: str,
    start: str | None = None,
    end: str | None = None,
    recency_days: int = 30,
) -> str:
    """
    Get enriched multi-collection context for a symbol: stocks KPIs, news, sentiment summary.

    Call this when the user asks for a complete market picture, e.g.,
    "Give me a full analysis of TSLA this month",
    "What is the overall sentiment for NVDA?".

    Args:
        symbol: Stock ticker symbol
        start: Start date YYYY-MM-DD (default: recency_days ago)
        end: End date YYYY-MM-DD (default: today)
        recency_days: Days for recency weighting (default: 30)

    Returns:
        JSON string with KPI summaries per collection.
    """
    import json
    from datetime import date, timedelta
    from src.agents.retriever import MarketRAGRetriever
    import polars as pl

    retriever = MarketRAGRetriever()

    end_dt = end or date.today().isoformat()
    start_dt = start or (date.today() - timedelta(days=recency_days)).isoformat()

    results: dict = {
        "symbol": symbol,
        "applied_filter": {"start": start_dt, "end": end_dt}
    }

    # Parallel queries to all 3 collections
    stock_data = retriever.query_by_metadata(
        collection="stocks", query="", symbol=symbol,
        start_date=start_dt, end_date=end_dt,
    )
    news_data = retriever.query_by_metadata(
        collection="news", query="", symbol=symbol,
        start_date=start_dt, end_date=end_dt,
    )
    sentiment_data = retriever.query_by_metadata(
        collection="sentiment", query="", symbol=symbol,
        start_date=start_dt, end_date=end_dt,
    )

    # -- Stocks summary --
    if stock_data:
        closes = [r["metadata"].get("close", 0.0) for r in stock_data]
        volumes = [r["metadata"].get("volume", 0) for r in stock_data]
        first_close, last_close = closes[0], closes[-1]
        period_return = round((last_close - first_close) / first_close * 100, 2) if first_close else 0.0
        volatility = round(float(pl.Series(closes).std() or 0.0), 2)
        avg_volume = int(sum(volumes) / len(volumes)) if volumes else 0
        trend = "bullish" if period_return > 2 else "bearish" if period_return < -2 else "neutral"
        recent_prices = [
            {"date": r["metadata"].get("date"), "close": r["metadata"].get("close")}
            for r in stock_data[-5:]
        ]
        results["stocks_summary"] = {
            "period_return_pct": period_return,
            "volatility": volatility,
            "avg_volume": avg_volume,
            "trend": trend,
            "recent_prices": recent_prices,
        }
    else:
        results["stocks_summary"] = {"status": "no_data"}

    # -- News summary --
    if news_data:
        scores = [r["metadata"].get("sentiment_score", 0.0) for r in news_data]
        positive = sum(1 for s in scores if s > 0.2)
        negative = sum(1 for s in scores if s < -0.2)
        neutral = len(scores) - positive - negative
        headlines = [
            {"date": r["metadata"].get("timestamp", "")[:10],
             "source": r["metadata"].get("source", ""),
             "headline": r["document"][:100]}
            for r in news_data[-5:]
        ]
        results["news_summary"] = {
            "article_count": len(news_data),
            "sentiment_distribution": {"positive": positive, "negative": negative, "neutral": neutral},
            "recent_headlines": headlines,
        }
    else:
        results["news_summary"] = {"status": "no_data"}

    # -- Sentiment summary --
    if sentiment_data:
        scores = [r["metadata"].get("sentiment_score", 0.0) for r in sentiment_data]
        avg_score = round(float(sum(scores) / len(scores)), 2) if scores else 0.0
        dominant = "positive" if avg_score > 0.1 else "negative" if avg_score < -0.1 else "neutral"
        scores_series = pl.Series(scores)
        half = len(scores) // 2
        first_half = scores_series.head(half).mean() if half > 0 else 0.0
        second_half = scores_series.tail(half).mean() if half > 0 else 0.0
        trend_dir = "improving" if second_half > first_half + 0.05 else "deteriorating" if second_half < first_half - 0.05 else "stable"
        scored = [
            {"date": r["metadata"].get("date"), "score": r["metadata"].get("sentiment_score", 0.0)}
            for r in sentiment_data
        ]
        sorted_score = sorted(scored, key=lambda x: x["score"], reverse=True)
        results["sentiment_summary"] = {
            "aggregate_score": avg_score,
            "dominant_sentiment": dominant,
            "sentiment_trend": trend_dir,
            "top_positive_days": sorted_score[:3],
            "top_negative_days": sorted_score[-3:],
        }
    else:
        results["sentiment_summary"] = {"status": "no_data"}

    # -- Missing collections --
    missing = []
    for col in ["stocks", "news", "sentiment"]:
        key = f"{col}_summary"
        if results.get(key, {}).get("status") == "no_data":
            missing.append(col)
    if missing:
        results["temporal_metadata"] = {"missing_collections": missing}

    # -- Prompt string --
    def _to_prompt() -> str:
        parts = [f"{symbol} Market Context ({start_dt} to {end_dt}):"]
        if results.get("stocks_summary") != {"status": "no_data"}:
            s = results["stocks_summary"]
            parts.append(
                f"STOCKS: {s['period_return_pct']}% return, "
                f"vol {s['volatility']}, avg vol {s['avg_volume']}M, trend: {s['trend']}"
            )
        if results.get("sentiment_summary") != {"status": "no_data"}:
            s = results["sentiment_summary"]
            parts.append(
                f"SENTIMENT: {s['aggregate_score']} ({s['dominant_sentiment']}), "
                f"trend: {s['sentiment_trend']}"
            )
        if results.get("news_summary") != {"status": "no_data"}:
            s = results["news_summary"]
            parts.append(
                f"NEWS: {s['article_count']} articles, "
                f"distribution: {s['sentiment_distribution']}"
            )
        return "\n".join(parts)

    results["prompt_estimate"] = len(_to_prompt())
    results["prompt_string"] = _to_prompt()

    return json.dumps(results)


def get_retriever_tools() -> list:
    """
    Get all retriever tools as LangChain tool list.

    Returns:
        List of LangChain Tool instances
    """
    return [
        query_stocks_tool,
        query_news_tool,
        query_sentiment_tool,
        query_all_tool,
        get_sentiment_price_correlation_tool,
        align_by_temporal_window_tool,
        get_cross_collection_context_tool,
    ]


__all__ = [
    "query_stocks_tool",
    "query_news_tool",
    "query_sentiment_tool",
    "query_all_tool",
    "get_sentiment_price_correlation_tool",
    "align_by_temporal_window_tool",
    "get_cross_collection_context_tool",
    "get_retriever_tools",
]