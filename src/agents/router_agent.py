"""RouterAgent — classifies queries and routes to the appropriate sub-orchestrator.

Has fall-back mechanism: when confidence < 0.7, queries ALL sub-orchestrators
and synthesizes results via LLM.
"""
from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
from src.agents.sub_orchestrator import BaseSubOrchestrator
from src.utils import get_logger

if TYPE_CHECKING:
    pass

log = get_logger("agents.router_agent")

_CONFIDENCE_THRESHOLD = 0.7


class RoutingDecision:
    """Result of routing a query."""
    
    def __init__(
        self,
        mode: str,
        sub_orchestrator: BaseSubOrchestrator | None = None,
        confidence: float = 0.0,
    ):
        self.mode = mode  # "direct" or "fallback"
        self.sub_orchestrator = sub_orchestrator
        self.confidence = confidence


class RouterAgent:
    """Routes queries to the correct sub-orchestrator based on domain."""
    
    def __init__(self) -> None:
        self.sub_orchestrators: list[BaseSubOrchestrator] = []
    
    def register(self, sub: BaseSubOrchestrator) -> None:
        """Register a sub-orchestrator."""
        self.sub_orchestrators.append(sub)
        log.info(f"🔄 Registered sub-orchestrator: {sub.domain}")
    
    def route(self, query: str) -> RoutingDecision:
        """Classify query and return routing decision.
        
        Returns the best match. If confidence < threshold, returns fallback mode.
        """
        if not self.sub_orchestrators:
            log.warning("⚠️ No sub-orchestrators registered!")
            return RoutingDecision(mode="fallback", confidence=0.0)
        
        best_sub = None
        best_conf = 0.0
        
        log.info(f"🔍 Routing query: '{query[:80]}...'")
        log.info(f"   Checking {len(self.sub_orchestrators)} sub-orchestrators:")
        
        for sub in self.sub_orchestrators:
            can, conf = sub.can_handle(query)
            log.info(f"   {sub.domain:15s} → can_handle={can}, confidence={conf:.2f}")
            if can and conf > best_conf:
                best_conf = conf
                best_sub = sub
        
        if best_sub and best_conf >= _CONFIDENCE_THRESHOLD:
            log.info(f"✅ ROUTED TO '{best_sub.domain}' (confidence={best_conf:.2f})")
            return RoutingDecision(
                mode="direct",
                sub_orchestrator=best_sub,
                confidence=best_conf,
            )
        
        log.info(f"⚠️ FALL-BACK triggered — best match: '{best_sub.domain if best_sub else 'NONE'}' (confidence={best_conf:.2f}, threshold={_CONFIDENCE_THRESHOLD})")
        log.info(f"   All sub-orchestrators will be queried and results synthesized.")
        return RoutingDecision(mode="fallback", confidence=best_conf)
    
    def answer(self, query: str) -> str:
        """Route the query and get an answer.
        
        Direct route: delegate to the best sub-orchestrator.
        Fall-back: query all in parallel, synthesize with LLM.
        """
        decision = self.route(query)
        
        if decision.mode == "direct" and decision.sub_orchestrator:
            return decision.sub_orchestrator.answer(query)
        
        # Fall-back: query all sub-orchestrators
        return self._fallback_answer(query)
    
    def _fallback_answer(self, query: str) -> str:
        """Query ALL sub-orchestrators and synthesize results."""
        results = []
        for sub in self.sub_orchestrators:
            try:
                result = sub.answer(query)
                results.append(f"--- {sub.domain.upper()} ---\n{result}")
            except Exception as e:
                log.warning(f"{sub.domain} sub-orchestrator failed: {e}")
                results.append(f"--- {sub.domain.upper()} ---\n(No disponible)")
        
        # Simple synthesis: combine results with separators
        combined = "\n\n".join(results)
        
        # Try LLM synthesis if available
        try:
            return self._synthesize_with_llm(query, combined)
        except Exception as e:
            log.warning(f"LLM synthesis failed, using raw combined: {e}")
            return combined
    
    def _synthesize_with_llm(self, query: str, context: str) -> str:
        """Use LLM to synthesize results from multiple domains."""
        try:
            from langchain_openai import ChatOpenAI
            from src.config import settings
            
            llm = ChatOpenAI(
                model=settings.rag_llm_model,
                temperature=0.3,
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
            )
            
            prompt = f"""Sos un analista financiero senior. El usuario preguntó:

"{query}"

Recibiste información de MÚLTIPLES FUENTES. Sintetizala en una respuesta coherente y ejecutiva.

DATOS DISPONIBLES:
{context}

Instrucciones:
- Integrá los datos de todas las fuentes en un análisis único
- Si hay datos contradictorios, señalalos
- Si una fuente no tiene datos, simplemente no la menciones
- Respondé en el mismo idioma de la consulta
- Formato: análisis ejecutivo en párrafos, sin bullet points de datos crudos"""
            
            response = llm.invoke([
                {"role": "system", "content": "Sos un analista financiero senior multi-mercado."},
                {"role": "user", "content": prompt},
            ])
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            log.warning(f"LLM synthesis failed: {e}")
            return context
