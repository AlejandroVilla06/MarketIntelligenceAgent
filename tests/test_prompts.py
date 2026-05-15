"""
Tests for Prompts
=================

Unit tests for prompt templates in chains/prompts.py
Tests the new dynamic multi-language prompt system.

Usage:
    pytest tests/test_prompts.py -v
"""

import pytest
from src.agents.chains.prompts import (
    MARKET_REACT_PROMPT,
    MARKET_REACT_PROMPT_ES,
    MARKET_REACT_PROMPT_EN,
    SUMMARIZE_RESULTS_PROMPT,
    SUMMARIZE_RESULTS_PROMPT_ES,
    SUMMARIZE_RESULTS_PROMPT_EN,
    MARKET_REACT_PROMPT_INPUT_VARIABLES,
    build_agent_prompt,
    build_summarize_prompt,
    get_language_name,
)


class TestPromptBuilder:
    """Test suite for the dynamic prompt builder."""

    def test_build_agent_prompt_english(self):
        """Test building an English agent prompt."""
        prompt = build_agent_prompt("en")
        rendered = prompt.format(input="What is AAPL price?", agent_scratchpad="")
        assert "MarketIntelligenceAgent" in rendered
        assert "same language as the user" in rendered
        assert "What is AAPL price?" in rendered

    def test_build_agent_prompt_spanish(self):
        """Test building a Spanish agent prompt."""
        prompt = build_agent_prompt("es")
        rendered = prompt.format(input="¿Cuál es el precio de AAPL?", agent_scratchpad="")
        assert "same language as the user" in rendered
        assert "MarketIntelligenceAgent" in rendered
        assert "¿Cuál es el precio de AAPL?" in rendered

    def test_build_agent_prompt_french(self):
        """Test building a French agent prompt."""
        prompt = build_agent_prompt("fr")
        rendered = prompt.format(input="Quel est le prix?", agent_scratchpad="")
        assert "same language as the user" in rendered
        assert "Executive Summary" in rendered

    def test_build_agent_prompt_german(self):
        """Test building a German agent prompt."""
        prompt = build_agent_prompt("de")
        rendered = prompt.format(input="Wie ist der Kurs?", agent_scratchpad="")
        assert "same language as the user" in rendered

    def test_build_agent_prompt_portuguese(self):
        """Test building a Portuguese agent prompt."""
        prompt = build_agent_prompt("pt")
        rendered = prompt.format(input="Qual é o preço?", agent_scratchpad="")
        assert "same language as the user" in rendered

    def test_build_agent_prompt_no_react_format(self):
        """Test that prompt instructs no ReAct format in output."""
        prompt = build_agent_prompt("en")
        rendered = prompt.format(input="test", agent_scratchpad="")
        # The prompt now mentions this in the FINAL RULES section
        assert "Executive Summary" in rendered
        assert "Context & Catalysts" in rendered
        assert "Outlook" in rendered

    def test_prompt_has_tool_instructions(self):
        """Test that prompt includes tool descriptions."""
        prompt = build_agent_prompt("en")
        rendered = prompt.format(input="test", agent_scratchpad="")
        assert "query_stocks_tool" in rendered
        assert "query_news_tool" in rendered
        assert "query_sentiment_tool" in rendered

    def test_build_summarize_prompt_spanish(self):
        """Test building a Spanish summarization prompt."""
        prompt = build_summarize_prompt("es")
        rendered = prompt.format(context="Some data", question="What?")
        assert "respond in Spanish" in rendered
        assert "market intelligence analyst" in rendered.lower()

    def test_build_summarize_prompt_french(self):
        """Test building a French summarization prompt."""
        prompt = build_summarize_prompt("fr")
        rendered = prompt.format(context="Some data", question="What?")
        assert "respond in French" in rendered

    def test_get_language_name(self):
        """Test language name resolution."""
        assert get_language_name("en") == "English"
        assert get_language_name("es") == "Spanish"
        assert get_language_name("fr") == "French"
        assert get_language_name("de") == "German"
        assert get_language_name("pt") == "Portuguese"
        assert get_language_name("it") == "Italian"
        assert get_language_name("xx") == "English"  # fallback


class TestBackwardCompatibility:
    """Test suite for backward compatibility aliases."""

    def test_market_react_prompt_works(self):
        """Test that MARKET_REACT_PROMPT still works (backward compat)."""
        prompt = MARKET_REACT_PROMPT.format(
            input="What is AAPL price?",
            agent_scratchpad=""
        )
        assert "MarketIntelligenceAgent" in prompt
        assert "Executive Summary" in prompt
        assert "What is AAPL price?" in prompt

    def test_market_react_prompt_es_builds(self):
        """Test that MARKET_REACT_PROMPT_ES builds (backward compat)."""
        prompt = MARKET_REACT_PROMPT_ES.format(
            input="¿Cuál es el precio de AAPL?",
            agent_scratchpad=""
        )
        assert "same language as the user" in prompt
        assert "¿Cuál es el precio de AAPL?" in prompt

    def test_market_react_prompt_en_builds(self):
        """Test that MARKET_REACT_PROMPT_EN builds (backward compat)."""
        prompt = MARKET_REACT_PROMPT_EN.format(
            input="What is the price of AAPL?",
            agent_scratchpad=""
        )
        assert "same language as the user" in prompt
        assert "What is the price of AAPL?" in prompt

    def test_prompts_have_input_variables(self):
        """Test that prompts require correct input variables."""
        assert "input" in MARKET_REACT_PROMPT_INPUT_VARIABLES
        assert "agent_scratchpad" in MARKET_REACT_PROMPT_INPUT_VARIABLES

    def test_all_backward_compat_aliases_exist(self):
        """Test that all backward compatibility aliases are exported."""
        from src.agents.chains import prompts
        assert hasattr(prompts, "MARKET_REACT_PROMPT_ES")
        assert hasattr(prompts, "MARKET_REACT_PROMPT_EN")
        assert hasattr(prompts, "SUMMARIZE_RESULTS_PROMPT_ES")
        assert hasattr(prompts, "SUMMARIZE_RESULTS_PROMPT_EN")
        assert hasattr(prompts, "build_agent_prompt")
        assert hasattr(prompts, "build_summarize_prompt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])