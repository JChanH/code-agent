# Code Agent

AI-powered code development agent built with Claude Agent SDK Python.

## Prerequisites

- **Node.js** v20+
- **Python** 3.11+
- **MySQL** 8.0 (외부)
- **Git** 2.30+

## Quick Start

### 1. Clone & Install

```bash
git clone <your-repo-url>
cd code-agent

# Install all dependencies
npm run install:all
```

### 2. Database Setup

```sql
CREATE DATABASE code_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your MySQL credentials and Anthropic API key
```

### 4. Run Development Server

```bash
# From project root — starts Frontend + Backend + Electron
npm run dev
```

Or run individually:

```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npx vite --port 5173

# Terminal 3: Electron
npx electron electron/main.js
```

### 5. Verify

- Backend health: http://localhost:8000/health
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

## Project Structure

```
code-agent/
├── frontend/          # React + Vite + TypeScript
├── backend/           # Python FastAPI + Claude Agent SDK
│   ├── app/
│   │   ├── api/       # REST API routes
│   │   ├── agents/    # Agent logic (Phase 2-3)
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic request/response schemas
│   │   ├── services/  # Git, Worktree services
│   │   └── websocket/ # Real-time updates
├── electron/          # Electron main process
└── shared/            # Shared types
```


