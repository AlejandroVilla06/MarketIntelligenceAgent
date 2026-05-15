"""
User Context — Perfil de Usuario para el Analista de Mercado
=============================================================

Permite que el agente conozca quién es el usuario y adapte su lenguaje,
ejemplos y nivel técnico en consecuencia.

Usage:
    from src.agents.user_context import ctx, setup_user_context

    # En app.py, al iniciar:
    setup_user_context(occupation="Data Science student", location="Medellín")

    # En query_agent.py, al construir el prompt:
    profile = ctx.get_profile_string()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserContext:
    """Perfil del usuario que el agente usa para adaptar sus respuestas.

    Attributes:
        name: Nombre del usuario (opcional).
        occupation: Ocupación (ej: "Data Science student").
        location: Ubicación (ej: "Medellín, Colombia").
        technical_level: Nivel técnico: "beginner" | "intermediate" | "advanced".
        interests: Lista de temas de interés.
        language: Idioma preferido (ISO 639-1).
        learning_goals: Metas de aprendizaje (opcional).
    """
    name: str = "Usuario"
    occupation: str = "Data Science student"
    location: str = "Medellín, Colombia"
    technical_level: str = "intermediate"
    interests: list[str] = field(default_factory=lambda: [
        "data science", "machine learning", "financial markets", "stock analysis",
    ])
    language: str = "es"
    learning_goals: str = "Aprender a analizar mercados financieros usando datos"


# Contexto singleton
_context = UserContext()


def setup_user_context(**kwargs: Any) -> None:
    """Configurar el perfil del usuario.

    Args:
        **kwargs: Campos a actualizar (name, occupation, location, etc.)
    """
    for key, value in kwargs.items():
        if hasattr(_context, key):
            setattr(_context, key, value)


def get_profile_string() -> str:
    """Obtener el perfil como texto formateado para el prompt.

    Returns:
        String descriptivo del usuario.
    """
    parts = [
        f"- **Ocupación**: {_context.occupation}",
        f"- **Ubicación**: {_context.location}",
        f"- **Nivel técnico**: {_context.technical_level}",
        f"- **Intereses**: {', '.join(_context.interests)}",
    ]
    if _context.learning_goals:
        parts.append(f"- **Objetivo**: {_context.learning_goals}")
    return "\n".join(parts)


def get_technical_level_instruction() -> str:
    """Obtener instrucción de adaptación de nivel técnico.

    Returns:
        Instrucción para el prompt según el nivel del usuario.
    """
    level = _context.technical_level
    if level == "beginner":
        return (
            "EXPLAIN concepts in simple terms. Avoid jargon without explanation. "
            "Use analogies. Define acronyms (RSI, PE ratio, etc.) the first time you use them."
        )
    elif level == "intermediate":
        return (
            "Use standard financial terminology but explain complex concepts briefly. "
            "Assume familiarity with basic metrics (PE, RSI, moving averages) but explain "
            "advanced concepts (correlation coefficients, options greeks, etc.)."
        )
    elif level == "advanced":
        return (
            "Use full financial jargon. Assume expert knowledge of derivatives, "
            "quantitative analysis, risk metrics, and market microstructure."
        )
    return ""


# Objeto conveniencia para importar: from src.agents.user_context import ctx
ctx = _context

__all__ = [
    "UserContext",
    "setup_user_context",
    "get_profile_string",
    "get_technical_level_instruction",
    "ctx",
]
