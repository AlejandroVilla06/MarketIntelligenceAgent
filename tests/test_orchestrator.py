"""
Tests for src.agents.orchestrator module (MarketOrchestrator).

Integration tests for orchestrator end-to-end flows.
Tests setup, ask, reset, and the full data pipeline.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


# Only run these tests if dependencies are available
try:
    import chromadb
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="Dependencies not available")


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
class TestMarketOrchestrator:
    """Test cases for MarketOrchestrator class."""

    @pytest.fixture
    def mock_storage(self):
        """Create mocked StorageInterface."""
        mock = MagicMock()
        
        import polars as pl
        from polars import DataFrame
        
        # Mock stock data
        mock.load_stocks.return_value = DataFrame({
            "date": ["2024-01-15", "2024-01-16"],
            "symbol": ["AAPL", "AAPL"],
            "close": [170.2, 171.5],
            "volume": [50000000, 55000000],
        })
        
        # Mock news data
        mock.load_news.return_value = DataFrame({
            "title": ["Apple Earnings", "Tech Rally"],
            "content": ["Strong results", "Tech sector up"],
            "source": ["Reuters", "Bloomberg"],
            "timestamp": ["2024-01-15T10:00:00", "2024-01-16T14:00:00"],
            "symbol": ["AAPL", "AAPL"],
        })
        
        # Mock sentiment data
        mock.load_sentiment.return_value = DataFrame({
            "symbol": ["AAPL", "AAPL"],
            "date": ["2024-01-15", "2024-01-16"],
            "sentiment_score": [0.75, 0.65],
            "sentiment_label": ["positive", "positive"],
        })
        
        return mock

    def test_orchestrator_can_be_imported(self):
        """Test that the orchestrator module can be imported."""
        from src.agents.orchestrator import MarketOrchestrator
        assert MarketOrchestrator is not None

    def test_init_sets_defaults(self):
        """Test initialization sets default values."""
        from src.agents.orchestrator import MarketOrchestrator
        
        orchestrator = MarketOrchestrator()
        
        assert orchestrator.persist_directory is None
        assert orchestrator.model_name is None
        assert orchestrator.retriever is None
        assert orchestrator.agent is None
        assert orchestrator._is_setup is False

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        from src.agents.orchestrator import MarketOrchestrator
        
        orchestrator = MarketOrchestrator(
            persist_directory="/custom/path",
            model_name="gpt-4",
        )
        
        assert orchestrator.persist_directory == "/custom/path"
        assert orchestrator.model_name == "gpt-4"

    def test_setup_initializes_components(self, tmp_path: Path):
        """Test that setup initializes retriever and agent."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.StorageInterface") as mock_storage:
            with patch("src.agents.orchestrator.MarketRAGRetriever") as mock_retriever:
                with patch("src.agents.orchestrator.MarketQueryAgent") as mock_agent:
                    # Set up mocks
                    mock_storage_instance = MagicMock()
                    mock_storage_instance.load_stocks.return_value = MagicMock()
                    mock_storage_instance.load_stocks.return_value.is_empty.return_value = False
                    mock_storage_instance.load_news.return_value = MagicMock()
                    mock_storage_instance.load_news.return_value.is_empty.return_value = False
                    mock_storage_instance.load_sentiment.return_value = MagicMock()
                    mock_storage_instance.load_sentiment.return_value.is_empty.return_value = True
                    mock_storage.return_value = mock_storage_instance
                    
                    mock_retriever_instance = MagicMock()
                    mock_retriever_instance._stocks_collection.count.return_value = 0
                    mock_retriever_instance._news_collection.count.return_value = 0
                    mock_retriever_instance._sentiment_collection.count.return_value = 0
                    mock_retriever.return_value = mock_retriever_instance
                    
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.run.return_value = "Test answer"
                    mock_agent.return_value = mock_agent_instance
                    
                    # Run setup
                    orchestrator = MarketOrchestrator(
                        persist_directory=str(tmp_path / "chromadb")
                    )
                    orchestrator.setup()
                    
                    # Verify setup completed
                    assert orchestrator._is_setup is True

    def test_ask_delegates_to_agent(self, tmp_path: Path):
        """Test that ask delegates to agent.run()."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.StorageInterface"):
            with patch("src.agents.orchestrator.MarketRAGRetriever") as mock_retriever:
                with patch("src.agents.orchestrator.MarketQueryAgent") as mock_agent:
                    mock_retriever_instance = MagicMock()
                    mock_retriever_instance._stocks_collection.count.return_value = 0
                    mock_retriever_instance._news_collection.count.return_value = 0
                    mock_retriever_instance._sentiment_collection.count.return_value = 0
                    mock_retriever.return_value = mock_retriever_instance
                    
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.run.return_value = "AAPL rose 3%"
                    mock_agent.return_value = mock_agent_instance
                    
                    orchestrator = MarketOrchestrator(
                        persist_directory=str(tmp_path / "chromadb")
                    )
                    orchestrator.setup()
                    
                    result = orchestrator.ask("How is AAPL?")
                    
                    mock_agent_instance.run.assert_called_once_with("How is AAPL?")

    def test_ask_returns_agent_result(self, tmp_path: Path):
        """Test that ask returns agent result."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.StorageInterface"):
            with patch("src.agents.orchestrator.MarketRAGRetriever"):
                with patch("src.agents.orchestrator.MarketQueryAgent") as mock_agent:
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.run.return_value = "Complete answer."
                    mock_agent.return_value = mock_agent_instance
                    
                    orchestrator = MarketOrchestrator()
                    orchestrator._is_setup = True
                    
                    result = orchestrator.ask("Test query")
                    
                    assert "Complete" in result

    def test_reset_clears_retriever_and_agent(self, tmp_path: Path):
        """Test that reset clears retriever and agent."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.MarketRAGRetriever") as mock_retriever:
            with patch("src.agents.orchestrator.MarketQueryAgent") as mock_agent:
                mock_retriever_instance = MagicMock()
                mock_retriever.return_value = mock_retriever_instance
                
                mock_agent_instance = MagicMock()
                mock_agent.return_value = mock_agent_instance
                
                orchestrator = MarketOrchestrator()
                orchestrator.retriever = mock_retriever_instance
                orchestrator.agent = mock_agent_instance
                orchestrator._is_setup = True
                
                orchestrator.reset()
                
                mock_retriever_instance.reset.assert_called_once()
                mock_agent_instance.reset.assert_called_once()
                assert orchestrator._is_setup is False

    def test_get_status_returns_setup_state(self, tmp_path: Path):
        """Test that get_status returns setup state."""
        from src.agents.orchestrator import MarketOrchestrator
        
        orchestrator = MarketOrchestrator()
        orchestrator._is_setup = True
        
        status = orchestrator.get_status()
        
        assert status["is_setup"] is True

    def test_get_status_returns_counts(self, tmp_path: Path):
        """Test that get_status returns collection counts."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.MarketRAGRetriever") as mock_retriever:
            mock_retriever_instance = MagicMock()
            mock_retriever_instance._stocks_collection.count.return_value = 100
            mock_retriever_instance._news_collection.count.return_value = 50
            mock_retriever_instance._sentiment_collection.count.return_value = 25
            mock_retriever.return_value = mock_retriever_instance
            
            orchestrator = MarketOrchestrator()
            orchestrator.retriever = mock_retriever_instance
            orchestrator._is_setup = True
            
            status = orchestrator.get_status()
            
            assert status["counts"]["stocks"] == 100
            assert status["counts"]["news"] == 50
            assert status["counts"]["sentiment"] == 25


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
class TestIntegrationFlows:
    """End-to-end integration tests (Task 4.3)."""

    def test_full_flow_setup_and_ask(self, tmp_path: Path):
        """Test full end-to-end flow with setup and ask."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.StorageInterface") as mock_storage:
            with patch("src.agents.orchestrator.MarketRAGRetriever") as mock_retriever:
                with patch("src.agents.orchestrator.MarketQueryAgent") as mock_agent:
                    # Set up mocks
                    mock_storage_instance = MagicMock()
                    mock_storage_instance.load_stocks.return_value = MagicMock()
                    mock_storage_instance.load_stocks.return_value.is_empty.return_value = False
                    mock_storage_instance.load_news.return_value = MagicMock()
                    mock_storage_instance.load_news.return_value.is_empty.return_value = True
                    mock_storage_instance.load_sentiment.return_value = MagicMock()
                    mock_storage_instance.load_sentiment.return_value.is_empty.return_value = True
                    mock_storage.return_value = mock_storage_instance
                    
                    mock_retriever_instance = MagicMock()
                    mock_retriever_instance._stocks_collection.count.return_value = 0
                    mock_retriever_instance._news_collection.count.return_value = 0
                    mock_retriever_instance._sentiment_collection.count.return_value = 0
                    mock_retriever.return_value = mock_retriever_instance
                    
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.run.return_value = "Complete answer."
                    mock_agent.return_value = mock_agent_instance
                    
                    # Create orchestrator
                    orchestrator = MarketOrchestrator(
                        persist_directory=str(tmp_path / "chromadb")
                    )
                    orchestrator.setup(storage=mock_storage_instance)
                    
                    # Verify setup
                    assert orchestrator._is_setup is True
                    assert orchestrator.retriever is not None
                    
                    # Execute ask
                    result = orchestrator.ask("Test query")
                    
                    # Verify result
                    assert result is not None

    def test_full_flow_ask_before_setup(self, tmp_path: Path):
        """Test that ask auto-sets up if needed."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.StorageInterface") as mock_storage:
            with patch("src.agents.orchestrator.MarketRAGRetriever"):
                with patch("src.agents.orchestrator.MarketQueryAgent") as mock_agent:
                    # Set up mock
                    mock_storage_instance = MagicMock()
                    mock_storage_instance.load_stocks.return_value = MagicMock()
                    mock_storage_instance.load_stocks.return_value.is_empty.return_value = True
                    mock_storage_instance.load_news.return_value = MagicMock()
                    mock_storage_instance.load_news.return_value.is_empty.return_value = True
                    mock_storage_instance.load_sentiment.return_value = MagicMock()
                    mock_storage_instance.load_sentiment.return_value.is_empty.return_value = True
                    mock_storage.return_value = mock_storage_instance
                    
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.run.return_value = "Test result"
                    mock_agent.return_value = mock_agent_instance
                    
                    # Create and ask without explicit setup
                    orchestrator = MarketOrchestrator(
                        persist_directory=str(tmp_path / "chromadb")
                    )
                    result = orchestrator.ask("Test query")
                    
                    # Should have auto-setup
                    assert orchestrator._is_setup is True
                    assert result is not None

    def test_ask_handles_error_gracefully(self, tmp_path: Path):
        """Test that ask handles agent errors gracefully."""
        from src.agents.orchestrator import MarketOrchestrator
        
        with patch("src.agents.orchestrator.StorageInterface"):
            with patch("src.agents.orchestrator.MarketRAGRetriever"):
                with patch("src.agents.orchestrator.MarketQueryAgent") as mock_agent:
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.run.side_effect = Exception("Test error")
                    mock_agent.return_value = mock_agent_instance
                    
                    orchestrator = MarketOrchestrator()
                    orchestrator._is_setup = True
                    
                    result = orchestrator.ask("Test query")
                    
                    # Should return error message, not raise
                    assert result is not None
                    assert "error" in result.lower() or "Error" in result