# Proposal: performance-opt

## Intent
Optimizar el rendimiento del frontend y backend para reducir tiempos de carga del bundle JS, comprimir respuestas API, y eliminar el falso streaming reemplazándolo con streaming real desde el LLM.

## Scope

### In Scope
1. Dynamic import de react-markdown (-80 kB bundle)
2. GZip compression middleware (respuestas 60-80% más chicas)
3. React.memo + useCallback en componentes clave
4. Real LLM streaming via StreamingCallbackHandler
5. LRU cache en memoria para queries repetidas
6. Optimización de middleware de Supabase

### Out of Scope
- Cache con Redis (externa)
- Migración a base de datos (Supabase persistence)
- Tests de performance automatizados (manual)

## Approach
3 fases incrementales: Quick Wins → Real Streaming → Polish

## Affected Areas
| File | Change |
|------|--------|
| frontend/src/components/ChatMessage.tsx | Dynamic import react-markdown + memo |
| frontend/src/components/MessageList.tsx | React.memo, fix key |
| frontend/src/components/Sidebar.tsx | React.memo |
| frontend/src/app/chat/page.tsx | useCallback |
| src/api/app.py | Add GZip middleware |
| src/agents/query_agent.py | Add streaming support |
| src/agents/orchestrator.py | Add ask_stream() |
| src/api/routes/chat.py | Use real streaming |
| src/agents/cache/semantic_cache.py | Add LRU hot cache |
| frontend/src/lib/supabase/middleware.ts | Optimize |
| frontend/next.config.mjs | Optimize |

## Risks
- Streaming fallback: algunos proveedores no soportan streaming
- React.memo: stale closures si no se declaran bien las deps
- LRU cache: consumo de memoria sin TTL

## Success Criteria
- [ ] Chat page bundle < 180 kB (-30%)
- [ ] GZip activo en respuestas API
- [ ] Streaming real: primer token < 3s
- [ ] Queries repetidas servidas desde cache
- [ ] Sin regresiones en tests (24/24 API tests)
