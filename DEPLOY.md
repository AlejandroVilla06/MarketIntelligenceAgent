# Deploy Guide — Market Intelligence Agent

> Ready-to-run instructions for deploying the backend on a **clean Linux server**
> (Ubuntu 22.04+ / Debian 12+). Agnostic to cloud provider (AWS, GCP, Azure,
> DigitalOcean, or bare metal).

---

## Prerequisites

| Tool     | Version    | Reason                                    |
|----------|------------|-------------------------------------------|
| Docker   | ≥ 24       | Container runtime                         |
| Docker Compose | ≥ 2.24 | Orchestration (standalone or plugin) |
| Git      | ≥ 2.34     | Clone the repository                      |

Verify:

```bash
docker --version          # Docker version 24.0.7+
docker compose version    # Docker Compose version 2.24+
git --version             # git version 2.34+
```

---

## Quick Start

```bash
# 1. Clone
git clone <your-repo-url> market-intelligence-agent
cd market-intelligence-agent

# 2. Set production credentials (one-time)
cat > .env << 'EOF'
# ── REQUIRED ────────────────────────────────────────────────────────────────
APP_ENV=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
SUPABASE_JWT_SECRET=your-jwt-secret-here
OPENAI_API_KEY=sk-or-v1-...
OPENAI_API_BASE=https://openrouter.ai/api/v1
COINMARKETCAP_API_KEY=your-coinmarketcap-key
FRED_API_KEY=your-fred-api-key

# ── OPTIONAL ────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
API_WORKERS=2
TRACKED_SYMBOLS=AAPL,GOOGL,NVDA,MSFT,AMZN
EOF

# 3. Build and start
docker compose up -d --build

# 4. Verify
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

---

## Production Deployment (No .env File)

For production, **never** store credentials in a `.env` file on disk.
Pass them directly to the container or use your orchestration layer's secrets
manager:

```bash
docker compose up -d --build -e SUPABASE_URL=... -e SUPABASE_KEY=...
```

Or better, set systemd environment variables (see [Systemd Integration](#systemd-integration) below).

> **Why?** The `get_settings()` function checks `APP_ENV=production` and
> **skips loading any `.env` file** — credentials come exclusively from
> system environment variables.

---

## Verify the Deployment

```bash
# Health check
curl -s http://localhost:8000/api/health | python -m json.tool
# → {"status":"ok"}

# API metadata
curl -s http://localhost:8000/api/status | python -m json.tool
# → {"status":"running","version":"1.0.0",...}

# Container logs
docker compose logs -f --tail=50
```

---

## Persistent Volumes

| Volume               | Mount Point                         | Content                         |
|----------------------|-------------------------------------|---------------------------------|
| `mia-chromadb-data`  | `/app/data/processed/chromadb`      | Vector database (ChromaDB)      |
| `mia-logs-data`      | `/app/logs`                         | Application logs                |
| `mia-raw-data`       | `/app/data/raw`                     | Downloaded market data          |

```bash
# Inspect volume location on host
docker volume inspect mia-chromadb-data --format '{{.Mountpoint}}'
```

To back up ChromaDB data:

```bash
docker run --rm -v mia-chromadb-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/chromadb-backup-$(date +%Y%m%d).tar.gz -C /data .
```

---

## Resource Tuning

The default `docker-compose.yml` sets:

| Resource | Limit   | Why                             |
|----------|---------|---------------------------------|
| Memory   | 4G max  | ChromaDB + torch + RAG pipeline |
| CPU      | Unbound | Let the OS scheduler decide     |

Adjust for your instance:

```yaml
# docker-compose.yml → api.deploy.resources
limits:
  memory: 8G        # Increase for large ChromaDB collections
  cpus: "2"         # Limit to 2 cores
reservations:
  memory: 2G
```

**Minimal instance**: 2 vCPU / 4 GB RAM (t3.medium, e2-standard-2).
**Recommended**: 4 vCPU / 8 GB RAM.

---

## Logs & Monitoring

```bash
# Tail live
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api

# Follow with timestamps
docker compose logs -f -t api
```

---

## Updating

```bash
git pull
docker compose up -d --build --pull=always
```

Zero-downtime updates require a load balancer in front (planned for a future
release).

---

## Systemd Integration

For production servers, manage the container with systemd for automatic
start on boot:

```bash
sudo tee /etc/systemd/system/mia-docker.service << 'EOF'
[Unit]
Description=Market Intelligence Agent (Docker Compose)
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/market-intelligence-agent
ExecStart=/usr/bin/docker compose up -d --build
ExecStop=/usr/bin/docker compose down
StandardOutput=journal

# ── Production credentials (NEVER in .env) ──────────────────────────────────
Environment=APP_ENV=production
Environment=SUPABASE_URL=https://your-project.supabase.co
Environment=SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
Environment=SUPABASE_JWT_SECRET=your-secret
Environment=OPENAI_API_KEY=sk-or-v1-...
Environment=COINMARKETCAP_API_KEY=your-key
Environment=FRED_API_KEY=your-key

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now mia-docker.service
```

---

## Troubleshooting

| Symptom                          | Likely Cause                         | Fix                                          |
|----------------------------------|--------------------------------------|----------------------------------------------|
| `/api/health` returns 503        | Orchestrator failed to init          | Check logs; missing `sentence_transformers`? |
| ChromaDB errors on restart       | Corrupted persistence                | `docker compose down -v` (deletes volume)    |
| Container exits immediately      | Missing required env var             | Verify `SUPABASE_URL`, `OPENAI_API_KEY` set  |
| Out of memory                    | torch + ChromaDB on small instance   | Reduce `API_WORKERS=1`, upgrade instance     |
| CORS errors from frontend        | `CORS_ORIGINS` not set               | Set `CORS_ORIGINS=https://your-frontend.com` |

---

## Security Checklist

- [ ] Credentials set via **system env vars**, never in `.env` in production
- [ ] Container runs as **non-root user** (UID 1001)
- [ ] `.dockerignore` excludes `.env`, `.git`, and secrets
- [ ] Health-check enabled (auto-restarts on failure)
- [ ] Volume permissions locked to UID 1001
- [ ] Supabase JWT secret rotated periodically
- [ ] API key for CoinMarketCap/FRED has minimal required permissions

---

## Architecture Diagram

```
                         ┌───────────────┐
                         │   Frontend    │
                         │  (Next.js)    │
                         └───────┬───────┘
                                 │ HTTPS
                                 ▼
                    ┌──────────────────────┐
                    │   API Server (:8000) │
                    │  FastAPI + Uvicorn   │
                    │  (this container)    │
                    └──┬───────┬───────┬───┘
                       │       │       │
              ┌────────┘       │       └────────┐
              ▼                ▼                 ▼
      ┌────────────┐   ┌────────────┐   ┌──────────────┐
      │ Supabase   │   │  LLM API   │   │  Market APIs │
      │ Auth+DB    │   │ (OpenAI,   │   │  (CMC, FRED) │
      │ (external) │   │  DeepSeek) │   │  (external)  │
      └────────────┘   └────────────┘   └──────────────┘

Volumes: chromadb_data, logs_data, raw_data
```
