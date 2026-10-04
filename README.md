# ShelfLife

ShelfLife is an AI-powered household kitchen companion designed to help people manage food around their household's needs. The product is in its foundation stage; the current application is a minimal frontend shell and health-check API.

## Project structure

```text
frontend/                 React, Vite, and TypeScript application
  src/services/           API client
  src/types/              API response types
backend/                  FastAPI application and tests
.github/workflows/        Continuous integration
.env.example              Placeholder environment variable names
master.md                 Product and architecture specification
logbook.md                Development history
```

## Development setup

Requirements: Node.js with npm, Python 3.12 or newer, and MongoDB Atlas for database-backed development.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Vite prints the local URL after the development server starts.

### Backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload
```

The health endpoint is available at `http://127.0.0.1:8000/api/health`.
With valid MongoDB configuration, `http://127.0.0.1:8000/api/health/db` performs a database ping.

### Backend tests

From the `backend/` directory, with the virtual environment activated:

```powershell
python -m pytest
```

## MongoDB configuration

Copy the root template, then edit `.env` locally:

```powershell
Copy-Item .env.example .env
```

Set these backend variables:

- `MONGODB_URI` — your MongoDB Atlas connection string.
- `MONGODB_DATABASE` — the database name ShelfLife should select.
- `VITE_API_BASE_URL` — optional frontend API base URL; local Vite development proxies `/api` to FastAPI by default.

Keep real credentials only in the local `.env` or your deployment's secret configuration; `.env` is ignored by Git. The application does not create collections or store application data yet.

## Future work

Household and inventory features, AI capabilities, and deployment are planned for later milestones and are not part of the current application.
