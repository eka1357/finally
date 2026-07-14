# FinAlly — AI Trading Workstation

Bloomberg-inspired dark trading terminal with live (or simulated) market data, a $10k paper portfolio, and an AI copilot that can analyze positions and execute trades.

## Features

- **Live price streaming** via SSE (green/red flash + sparklines)
- **GBM market simulator** by default; **Massive/Polygon** when `MASSIVE_API_KEY` is set
- **Paper portfolio** — market orders, positions, heatmap, P&L history
- **Watchlist** management
- **AI chat** — LiteLLM → OpenRouter (Cerebras) with structured trade actions
- **Single-port deploy** — Next.js static export served by FastAPI on `:8000`

## Quick start (Docker)

```bash
cp .env.example .env
# Add OPENROUTER_API_KEY and optionally MASSIVE_API_KEY

# Windows
.\scripts\start_windows.ps1 -Build

# macOS / Linux
chmod +x scripts/*.sh
./scripts/start_mac.sh --build
```

Open **http://localhost:8000**

Stop:

```bash
.\scripts\stop_windows.ps1   # Windows
./scripts/stop_mac.sh        # macOS/Linux
```

Or: `docker compose up --build`

## Local development

### Backend

```powershell
cd backend
uv sync --extra dev
# loads ../.env automatically
uv run uvicorn app.main:app --reload --port 8000
```

Tests:

```powershell
cd backend
uv run pytest -v
```

### Frontend

```powershell
cd frontend
npm.cmd install
$env:NEXT_PUBLIC_API_BASE = "http://localhost:8000"
npm.cmd run dev
```

Open **http://localhost:3000** (API on 8000).

### Production-like local (static UI on FastAPI)

```powershell
cd frontend
npm.cmd install
npm.cmd run build
# copy export into backend static
Remove-Item -Recurse -Force ..\backend\static -ErrorAction SilentlyContinue
Copy-Item -Recurse out ..\backend\static
cd ..\backend
uv run uvicorn app.main:app --port 8000
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | For real AI | OpenRouter key (Cerebras provider) |
| `MASSIVE_API_KEY` | No | Real market data; empty → simulator |
| `LLM_MOCK` | No | `true` for deterministic mock chat |
| `DB_PATH` | No | SQLite path (default `db/finally.db`) |
| `PORT` | No | Server port (default 8000) |

## Project layout

```
finally/
├── frontend/     # Next.js (static export)
├── backend/      # FastAPI + market data + portfolio + chat
├── planning/     # Specs for agents
├── scripts/      # start/stop + local dev helpers
├── test/         # Playwright smoke + docker-compose.test.yml
├── db/           # SQLite volume mount target
└── Dockerfile
```

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health |
| GET | `/api/stream/prices` | SSE prices |
| GET/POST/DELETE | `/api/watchlist` | Watchlist |
| GET/POST | `/api/portfolio`, `/api/portfolio/trade` | Portfolio & trades |
| GET | `/api/portfolio/history` | P&L snapshots |
| POST | `/api/chat` | AI assistant |

## License

See [LICENSE](LICENSE).
