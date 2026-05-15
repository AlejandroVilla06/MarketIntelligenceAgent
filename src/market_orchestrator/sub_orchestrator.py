"""Base class for all sub-orchestrators in the hierarchical system."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any


class BaseSubOrchestrator(ABC):
    """Abstract base for all sub-orchestrators.
    
    Each sub-orchestrator handles a specific domain (stocks, crypto, macro, calculations).
    """
    
    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain name: 'stocks', 'crypto', 'macro', 'calculation'."""
        ...
    
    @abstractmethod
    def can_handle(self, query: str) -> tuple[bool, float]:
        """Check if this orchestrator can handle the query.
        
        Returns:
            Tuple of (can_handle: bool, confidence: float 0.0-1.0)
        """
        ...
    
    @abstractmethod
    def answer(self, query: str) -> str:
        """Generate an answer for the query.
        
        Args:
            query: User's question
            
        Returns:
            Analysis/response string
        """
        ...
