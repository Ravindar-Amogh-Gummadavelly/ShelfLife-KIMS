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

Requirements: Node.js with npm, and Python 3.12 or newer.

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

### Backend tests

From the `backend/` directory, with the virtual environment activated:

```powershell
python -m pytest
```

## Environment variables

`.env.example` lists placeholder names for future configuration. Copy it to a local `.env` only when a feature requires those settings, then fill values locally. Real `.env` files are ignored by Git. The current foundation does not read environment variables or connect to external services.

## Future work

Database integration, household and inventory features, AI capabilities, and deployment are planned for later milestones and are not part of the current application.
