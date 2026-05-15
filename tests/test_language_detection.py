"""
Tests for Language Detection
=============================

Unit tests for the detect_language function in query_agent.py.
Now tests 6 languages: EN, ES, FR, DE, PT, IT.

Usage:
    pytest tests/test_language_detection.py -v
"""

import pytest
from src.agents.query_agent import detect_language, get_empathetic_greeting


class TestDetectLanguage:
    """Test suite for multi-language detection function."""

    # --- English ---

    def test_detect_english_greeting(self):
        """Test that English greetings are detected."""
        assert detect_language("hello") == "en"
        assert detect_language("hi how are you") == "en"
        assert detect_language("hey") == "en"

    def test_detect_english_market_query(self):
        """Test English market-related queries."""
        assert detect_language("how is AAPL doing today") == "en"
        assert detect_language("what is the price of NVDA") == "en"
        assert detect_language("stock market news this week") == "en"

    def test_detect_english_farewell(self):
        """Test English farewells."""
        assert detect_language("thanks for your help") == "en"
        assert detect_language("please show me") == "en"

    # --- Spanish ---

    def test_detect_spanish_greeting(self):
        """Test that Spanish greetings are detected."""
        assert detect_language("hola") == "es"
        assert detect_language("buenos días") == "es"
        assert detect_language("qué tal como estás") == "es"

    def test_detect_spanish_market_query(self):
        """Test Spanish market-related queries."""
        assert detect_language("cómo están las acciones de Apple") == "es"
        assert detect_language("dime el precio de NVDA") == "es"
        assert detect_language("quiero saber sobre la bolsa") == "es"

    def test_detect_spanish_with_accents(self):
        """Test Spanish words with accents."""
        assert detect_language("cuál es el precio") == "es"
        assert detect_language("dónde puedo invertir") == "es"

    # --- French ---

    def test_detect_french_greeting(self):
        """Test that French greetings are detected."""
        assert detect_language("bonjour") == "fr"
        assert detect_language("salut comment ça va") == "fr"

    def test_detect_french_market_query(self):
        """Test French market-related queries."""
        assert detect_language("quel est le prix de l'action Apple") == "fr"
        assert detect_language("comment se porte le marché aujourd'hui") == "fr"

    # --- German ---

    def test_detect_german_greeting(self):
        """Test that German greetings are detected."""
        assert detect_language("guten Tag wie geht es Ihnen") == "de"

    def test_detect_german_market_query(self):
        """Test German market-related queries."""
        assert detect_language("wie hat sich die Aktie von Tesla entwickelt") == "de"
        assert detect_language("zeig mir den Aktienkurs von AAPL") == "de"

    # --- Portuguese ---

    def test_detect_portuguese_greeting(self):
        """Test that Portuguese greetings are detected."""
        assert detect_language("olá bom dia") == "pt"

    def test_detect_portuguese_market_query(self):
        """Test Portuguese market-related queries."""
        assert detect_language("qual é o preço das ações da Apple") == "pt"
        assert detect_language("como está o mercado hoje") == "pt"

    # --- Italian ---

    def test_detect_italian_greeting(self):
        """Test that Italian greetings are detected."""
        assert detect_language("ciao come stai") == "it"

    def test_detect_italian_market_query(self):
        """Test Italian market-related queries."""
        assert detect_language("qual è il prezzo delle azioni Apple") == "it"

    # --- Edge cases ---

    def test_empty_query_returns_english(self):
        """Test that empty query defaults to English."""
        assert detect_language("") == "en"
        assert detect_language("   ") == "en"

    def test_numbers_only(self):
        """Test that numbers only default to English."""
        assert detect_language("123456") == "en"

    def test_short_ticker_symbol_returns_english(self):
        """Test that ticker symbols default to English."""
        assert detect_language("AAPL") == "en"
        assert detect_language("NVDA") == "en"

    def test_mixed_language_falls_back(self):
        """Test that mixed language picks the best match."""
        result = detect_language("hola how are you")
        assert result in ["es", "en"]


class TestEmpatheticGreeting:
    """Test suite for multi-language empathetic greeting function."""

    def test_spanish_greeting(self):
        """Test Spanish greeting."""
        greeting = get_empathetic_greeting("es")
        assert "Hola" in greeting or "hola" in greeting.lower()
        assert "mercado" in greeting or "análisis" in greeting

    def test_english_greeting(self):
        """Test English greeting."""
        greeting = get_empathetic_greeting("en")
        assert "Hello" in greeting or "hello" in greeting.lower()
        assert "market" in greeting or "assistant" in greeting

    def test_french_greeting(self):
        """Test French greeting."""
        greeting = get_empathetic_greeting("fr")
        assert "Bonjour" in greeting

    def test_german_greeting(self):
        """Test German greeting."""
        greeting = get_empathetic_greeting("de")
        assert "Hallo" in greeting

    def test_portuguese_greeting(self):
        """Test Portuguese greeting."""
        greeting = get_empathetic_greeting("pt")
        assert "Olá" in greeting

    def test_italian_greeting(self):
        """Test Italian greeting."""
        greeting = get_empathetic_greeting("it")
        assert "Ciao" in greeting

    def test_unknown_language_fallsback_to_english(self):
        """Test unknown language code falls back to English."""
        greeting = get_empathetic_greeting("xx")
        assert "Hello" in greeting

    def test_greeting_has_emoji(self):
        """Test all greetings have wave emoji."""
        for lang in ["en", "es", "fr", "de", "pt", "it"]:
            assert "👋" in get_empathetic_greeting(lang), f"Missing emoji for {lang}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])