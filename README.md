# WinTAI

A fully local Windows AI assistant — monorepo.

## Architecture

```
WinTAI/
├── apps/
│   ├── frontend/          # React + Vite + TypeScript + Electron — UI layer
│   │   ├── electron/      # Electron main process & preload
│   │   └── src/           # React source
│   └── backend/           # Python FastAPI — API orchestrator
│
├── packages/
│   ├── shared/            # Shared types and schemas (ToolRequest, etc.)
│   ├── tools/             # Static tool definitions (no execution logic)
│   └── core/              # Placeholder for future shared logic
│
├── services/
│   ├── embeddings/        # Sentence-transformers embedding + vector index
│   ├── executor/          # Interface-only placeholder
│   └── registry/          # Tool registry (JSON-backed)
│
└── infra/
    ├── scripts/           # Dev setup and run scripts
    ├── setup/             # Setup documentation
    └── configs/           # Shared config files (linter, CI)
```

## Layer Responsibilities

| Layer | Responsibility |
|---|---|
| `apps/frontend` | Pure UI — no business logic, no system access |
| `apps/backend` | API orchestrator — no business logic, routes to services |
| `packages/shared` | Contracts only — TypeScript types, no runtime |
| `packages/tools` | Static tool definitions only — open_app, open_url |
| `services/embeddings` | Placeholder interface for future intent detection |
| `services/executor` | Placeholder interface for future Windows command execution |
| `services/registry` | Placeholder interface for future tool/action registry |
| `infra` | Dev tooling, scripts, shared configs |

## Getting Started

### Backend

```bash
cd apps/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

API: `http://127.0.0.1:8000` — Docs: `http://127.0.0.1:8000/docs`

### Frontend (Browser)

```bash
cd apps/frontend
npm install
npm run dev
```

UI: `http://localhost:5173`

### Frontend (Desktop App)

```bash
cd apps/frontend
npm install
npm run electron:dev       # Development with hot reload
# or
npm run electron:build     # Production build + package into installer
```

The desktop app launches a native window connecting to the backend at `http://127.0.0.1:8000`.

### Packaging

To build a distributable Windows installer:

```bash
cd apps/frontend
npm run electron:build
```

Output: `apps/frontend/release/WinTAI Setup X.X.X.exe`
