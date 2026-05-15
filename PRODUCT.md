# Market Intelligence Agent — Smart Financial Terminal

## Elevator Pitch

Una terminal financiera inteligente que unifica crypto, macro y equities en un solo chat conversacional, con respuestas en tu idioma y datos renderizados como widgets visuales en tiempo real. Para data scientists y quants latinoamericanos que necesitan velocidad sin sacrificar profundidad analítica.

---

## Visión

Ser la terminal financiera inteligente definitiva para data scientists y quants latinoamericanos. La plataforma donde el analista financiero del sur global deja de saltar entre Bloomberg Terminal, TradingView, CoinGecko y FRED, y ejecuta todo desde un solo chat que entiende español, portugués e inglés, y responde con datos vivos, gráficos y widgets — no texto plano.

> **Norte estratégico**: Democratizar el acceso a inteligencia financiera de nivel institucional para TODO el ecosistema LATAM, eliminando la fricción del idioma, la dispersión de fuentes y la complejidad técnica.

---

## Hypothesis-Driven Development (HDD)

Cada decisión de producto se valida contra hipótesis falsables. Medimos, aprendemos, pivotamos.

### Hipótesis 1: Velocidad de decisión multiclase

> **Si** los analistas tienen datos en tiempo real de crypto + macro + equities en un **solo chat**,  
> **entonces** toman decisiones **3x más rápido** que usando fuentes separadas.

- **Métrica clave**: Tiempo promedio entre consulta inicial y decisión documentada (línea base: ~45 min con fuentes separadas, target: ≤15 min)
- **Falsable si**: después de 4 semanas con 50 usuarios activos, la mediana de tiempo por consulta-compra no se reduce al menos 2x

### Hipótesis 2: Adopción por idioma nativo

> **Si** el sistema responde en el **idioma del usuario** (ES/PT/EN),  
> **entonces** la adopción en LATAM es **2x más rápida** que una solución solo en inglés.

- **Métrica clave**: Tasa de registro → usuario activo día 7 (activación) segmentada por idioma
- **Falsable si**: después de 8 semanas, la cohorte ES/PT no muestra retención semanal ≥ 1.5x vs cohorte EN

### Hipótesis 3: Comprensión visual

> **Si** los datos se renderizan como **widgets visuales** (gráficos, tablas, indicadores) en lugar de texto,  
> **entonces** la comprensión es **5x más rápida** medida como tiempo hasta respuesta correcta en preguntas de análisis.

- **Métrica clave**: Precisión de respuestas en preguntas de análisis cuantitativo (ej. "¿qué tendencia muestra BTC este mes?")
- **Falsable si**: usuarios con widgets visuales no responden correctamente al menos 80% de las preguntas en <30 segundos

---

## Arquitectura de valor

Cómo fluye el valor desde que el usuario pregunta hasta que recibe una respuesta accionable:

```
User → Chat Interface → RouterAgent → Sub-Orchestrators → MCP Tools → Supabase
│        │                  │               │                  │            │
│        │                  │               │                  │            │
├─ ES/PT/EN                ├─ Clasifica    ├─ Stocks           ├─ yfinance  ├─ Auth
│  input                    │  intención    ├─ Crypto           ├─ CoinGecko │─ Chat history
│                          │  y confianza  ├─ Macro            ├─ FRED      ├─ User profiles
│                          │  (≥0.7 directo,│─ Calculation     ├─ Alpha     ├─ Vector store
│                          │   <0.7 fallback│                  │  Vantage   │─ Cache
│                          │   paralelo)   │                  ├─ Polygon.io│
│                          │               │                  ├─ LLM (RAG) │
│                          │               │                  └─ Python REPL│
```

Cada capa tiene una responsabilidad única y reemplazable. El RouterAgent es el cerebro: clasifica, delega o sintetiza. Los Sub-Orchestrators son los especialistas. MCP Tools son los músculos que traen datos del mundo real. Supabase es la memoria del sistema.

---

## Roadmap

### ✅ Lo que ya tenemos (8 cambios archivados)

| Sprint | Cambio | Estado |
|--------|--------|--------|
| Sprint 1 | Data Ingestion — stocks, crypto, macro pipelines | ✅ Archivado |
| Sprint 2 | ML Models — feature engineering, trend prediction, anomaly detection | ✅ Archivado |
| Sprint 3 | RAG Agents — market query agent, retriever, cross-collection context | ✅ Archivado |
| Sprint 3 | Sentiment Analysis — Llama-based news sentiment ingestion | ✅ Archivado |
| Sprint 4 | RAG + Sentiment — temporal alignment, sentiment-price correlation | ✅ Archivado |
| Sprint 5 | RAG Latency Optimization — semantic query cache, benchmarking | ✅ Archivado |
| Sprint 6 | Streamlit UI — glassmorphism dashboard, empathetic agent, sidebar | ✅ Archivado |
| Sprint 7 | Agent UI Overhaul — chatGPT dashboard, multi-language, NL agent | ✅ Archivado |

Además: Supabase auth + persistence, Next.js frontend, pnpm migration, hierarchical multi-market orchestrator, silent context pipeline, performance optimization, y más — todo entregado.

### 🔜 Lo que viene

| Iniciativa | Por qué importa |
|-----------|----------------|
| **User Settings & Preferences** | Perfil de usuario configurable: idioma, mercado default, widgets favoritos, alertas personalizadas. Sin esto, cada sesión empieza desde cero. |
| **Deployment & DevOps** | Pipeline CI/CD, Docker, staging/producción, monitoreo. El producto no existe si no está en producción con uptime 99.9%. |
| **Onboarding Interactivo** | Primera experiencia guiada para que un nuevo usuario vea valor en <2 minutos. Crítico para reducir churn día 0→1. |
| **Alertas Inteligentes** | Notificaciones proactivas basadas en umbrales de precio, sentimiento o anomalías detectadas por ML. |
| **Modo Offline / Datos Diferidos** | Consultas sobre datos cacheados sin conexión, con sync automático al reconectar. Para analistas en movimiento. |

---

## Métricas de éxito

Lo que no se mide no se mejora. Estas son las métricas que definen si el producto está cumpliendo su visión:

### Engagement
| Métrica | Target | Por qué |
|---------|--------|---------|
| **DAU (Daily Active Users)** | ≥ 200 usuarios únicos/día a los 6 meses | Mide tracción real, no registros vanity |
| **Tiempo por consulta** | ≤ 8 segundos (p95) | La velocidad ES la feature |
| **Consultas por sesión** | ≥ 5 por usuario activo | Indica que el chat resuelve problemas reales, no es un juguete |

### Calidad
| Métrica | Target | Por qué |
|---------|--------|---------|
| **Precisión de respuestas** | ≥ 90% evaluado por expertos | Sin precisión, no hay confianza. Sin confianza, no hay producto. |
| **Tasa de fallback a LLM general** | ≤ 15% | El RouterAgent debe clasificar correctamente la mayoría de consultas |

### Retención
| Métrica | Target | Por qué |
|---------|--------|---------|
| **Retención Semanal (W1 → W4)** | ≥ 40% | Un producto financiero sin retención es una demo |
| **NPS (Net Promoter Score)** | ≥ 40 | Los usuarios LATAM recomiendan o no. El NPS mide si aman el producto |

---

## Principios de producto

1. **Velocidad sobre features** — una consulta en <3 segundos vale más que 10 fuentes de datos que tardan 30 segundos
2. **Idioma nativo no es opcional** — si no hablamos español y portugués fluidamente, no estamos resolviendo el problema de LATAM
3. **Visual primero, texto después** — un gráfico bien renderizado elimina párrafos de explicación
4. **Datos vivos, no capturas** — cada widget debe actualizarse en tiempo real o indicar claramente su timestamp
5. **El chat es la interfaz, no el límite** — el chat es la puerta de entrada, pero la respuesta puede ser un dashboard completo

---

*Este documento define el "por qué" y "para qué" del Market Intelligence Agent. Cada sprint, cada tarea, cada línea de código debe responder a una de estas hipótesis o métricas. Si no, no lo construimos.*
