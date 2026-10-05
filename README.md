# AI Resume Analyzer

An intelligent, full-stack web application that evaluates PDF resumes against job descriptions, computes ATS compatibility scores, detects skill and keyword gaps, provides quantifiable bullet point rewrites, and prepares custom interview questions.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [1. Backend Setup](#1-backend-setup)
  - [2. Frontend Setup](#2-frontend-setup)
- [Environment Variables](#environment-variables)
- [AI Provider Configuration](#ai-provider-configuration)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Database & Migrations](#database--migrations)
- [Security & Privacy](#security--privacy)
- [Known Limitations & Future Improvements](#known-limitations--future-improvements)

---

## Overview

Applying for jobs often feels like a black box. **AI Resume Analyzer** gives candidates immediate, recruiter-level visibility into how well their resume aligns with any job posting.

It parses text from uploaded PDFs in-memory, extracts skills and key requirements, and utilizes an AI layer (OpenAI GPT-4o, Google Gemini, or an offline heuristic fallback) to return structured, calibrated analysis.

---

## Key Features

1. **Resume Upload & In-Memory Extraction**
   - Drag-and-drop or file browser for PDF resumes.
   - Strict size (5 MB default) and type validation.
   - Robust PDF text extraction via `pypdf` with graceful handling of corrupt, password-protected, empty, or scanned PDFs.
   - Temporary file avoidance: all parsing is done safely in memory.

2. **Job Description Parsing**
   - Clean textarea input with real-time character count and validation.
   - Automatic extraction of job titles, required hard skills, experience levels, and degrees.

3. **ATS Compatibility & AI Analysis**
   - **Overall ATS Score (0–100)**: Calibrated match score with visual animated circular gauge.
   - **Score Breakdown**: Sub-scores across Skills, Experience, Education, Projects, and Keywords.
   - **Skills Alignment**: Clear side-by-side chips for matching skills vs missing/desired skills.
   - **Keyword Coverage**: Filterable table of keywords with importance levels and frequency counts.
   - **Impact-Driven Bullet Rewrites**: Transform weak bullet points into strong, quantified statements (XYZ formula) with one-click clipboard copying.
   - **Recommended Projects**: Concrete project suggestions with target tech stacks to bridge identified gaps.
   - **Targeted Interview Questions**: Categorized technical, behavioral, experience, and skill-gap questions with rationale.

4. **Interactive Dashboard**
   - Premium dark-mode UI with glassmorphism, responsive grid, and accessible typography.
   - Live progress indicator with multi-stage status updates during analysis.

5. **Local History Management**
   - Previous analyses stored locally in SQLite.
   - Reopen past reports at any time.
   - Delete analyses with instant feedback and toast notifications.

6. **Pluggable AI Provider with Offline Fallback**
   - First-class abstraction for OpenAI, Google Gemini, and a deterministic offline heuristic analyzer.
   - Zero API key required for full local demonstration.

---

## Architecture & Tech Stack

```
   ┌────────────────────────────────────────────────────────┐
   │                  React 19 + TypeScript                 │
   │               Vite + React Router + CSS                │
   │             (Accessible, Mobile-Responsive)            │
   └───────────────────────────┬────────────────────────────┘
                               │ HTTP / JSON
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │                     FastAPI App                        │
   │           Pydantic v2 Schemas + CORS + Uvicorn         │
   └───────────────┬────────────────────────┬───────────────┘
                   │                        │
                   ▼                        ▼
      ┌───────────────────────┐  ┌───────────────────────┐
      │      SQLAlchemy 2     │  │   LLMProvider Layer   │
      │    Repository Pattern │  │ (OpenAI / Gemini /    │
      │   (SQLite / Postgres) │  │  Offline Mock Heuristic│
      └───────────────────────┘  └───────────────────────┘
```

### Backend
- **Python 3.11+ / 3.13**
- **FastAPI**: Modern, high-performance async/sync web framework.
- **Pydantic v2 & Pydantic-Settings**: Strict validation and typed settings.
- **SQLAlchemy 2.0**: Database abstraction using the Repository pattern (PostgreSQL-ready).
- **pypdf**: Robust, in-memory PDF extraction and inspection.
- **httpx**: Resilient HTTP client for external AI providers.
- **pytest & FastAPI TestClient**: Comprehensive test suite (71 tests).

### Frontend
- **React 19 & TypeScript**
- **Vite 8**: Ultra-fast build tool and dev server with proxy support.
- **React Router 7**: Client-side routing (`/`, `/analyses/:id`, `/history`).
- **Vanilla CSS (Design System)**: Bespoke CSS tokens, glassmorphism, dark palette, smooth animations.
- **Vitest & React Testing Library**: Component and unit tests (23 tests).

---

## Project Structure

```
AI Resume Analyzer/
├── backend/
│   ├── .env.example              # Environment variables template
│   ├── requirements.txt          # Production dependencies
│   ├── requirements-dev.txt      # Testing and development dependencies
│   ├── pytest.ini                # Pytest configuration
│   ├── create_sample_resume.py   # CLI tool to generate sample resume PDF
│   ├── app/
│   │   ├── main.py               # FastAPI application factory & lifespan
│   │   ├── api/
│   │   │   ├── deps.py           # Dependency injection wiring
│   │   │   └── routes/
│   │   │       ├── health.py     # GET /api/health
│   │   │       └── analyses.py   # POST /api/analyze, GET/DELETE /api/analyses
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic BaseSettings
│   │   │   ├── exceptions.py     # Domain exceptions & error handlers
│   │   │   └── logging.py        # Centralized logging configuration
│   │   ├── db/
│   │   │   ├── base.py           # SQLAlchemy declarative base
│   │   │   ├── models.py         # Analysis ORM model
│   │   │   ├── repository.py     # Data-access repository
│   │   │   └── session.py        # Engine and session lifecycle
│   │   ├── llm/
│   │   │   ├── base.py           # LLMProvider abstract interface
│   │   │   ├── factory.py        # Provider factory with auto-fallback
│   │   │   ├── prompts.py        # System prompt & JSON schema injection
│   │   │   ├── openai_provider.py# OpenAI chat completion provider
│   │   │   ├── gemini_provider.py# Google Gemini generative language provider
│   │   │   └── mock_provider.py  # Deterministic offline heuristic provider
│   │   ├── schemas/
│   │   │   └── analysis.py       # Pydantic schemas (AnalysisResult, etc.)
│   │   └── services/
│   │       ├── analysis_service.py # Core orchestration service
│   │       ├── pdf_extractor.py  # In-memory PDF validation & extraction
│   │       └── text_analysis.py  # Skill catalogs, keywords, and metrics
│   └── tests/
│       ├── conftest.py           # Fixtures (in-memory SQLite, test client)
│       ├── pdf_factory.py        # Programmatic PDF generation for tests
│       ├── test_api.py           # Endpoints, validation, and CRUD tests
│       ├── test_analysis.py      # Schema contract, mock, and LLM tests
│       ├── test_pdf_extractor.py # Corrupt/empty/valid PDF tests
│       └── test_repository.py    # Database layer tests
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts            # Vite config with API proxy & Vitest
│   ├── index.html                # App entry HTML with Google Fonts
│   └── src/
│       ├── main.tsx              # React DOM mounting
│       ├── App.tsx               # Router & providers
│       ├── index.css             # Core design tokens & utilities
│       ├── api/
│       │   └── client.ts         # Typed fetch client with ApiError mapping
│       ├── types/
│       │   └── analysis.ts       # TypeScript interfaces matching API schema
│       ├── lib/
│       │   ├── format.ts         # Score colors, labels, date formatters
│       │   └── validation.ts     # Client-side validation helpers
│       ├── components/
│       │   ├── common/           # Card, Icon, Toast, States
│       │   ├── analyze/          # Dropzone, JD textarea, Progress, Form
│       │   ├── dashboard/        # ScoreRing, Breakdown, Chips, Table, Lists
│       │   ├── history/          # HistoryList, History cards
│       │   └── layout/           # Header, Footer, Layout
│       ├── pages/
│       │   ├── AnalyzePage.tsx   # Upload & form page
│       │   ├── ResultPage.tsx    # Detailed dashboard report page
│       │   └── HistoryPage.tsx   # History listing & deletion page
│       └── test/
│           ├── setup.ts          # Vitest testing setup
│           ├── format.test.ts    # Format utility tests
│           ├── validation.test.ts# Validation tests
│           ├── ScoreRing.test.tsx# Score gauge component test
│           ├── AnalyzeForm.test.tsx # Form submission & error tests
│           └── HistoryList.test.tsx # History list & delete action tests
│
├── sample_resume.pdf             # Ready-to-use sample resume PDF
├── verify_e2e_live.py            # Live end-to-end integration test runner
└── README.md
```

---

## Prerequisites

- **Python 3.11+** (tested with Python 3.13)
- **Node.js 18+** and **npm 9+** (tested with Node 24 and npm 11)

---

## Quick Start

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\activate

# macOS / Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment settings
cp .env.example .env

# Start development server
uvicorn app.main:app --reload --port 8000
```

The backend will be running at `http://127.0.0.1:8000`.
Interactive API docs are available at `http://127.0.0.1:8000/api/docs`.

### 2. Frontend Setup

In a new terminal window:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

Open your browser at `http://127.0.0.1:5173`.

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure as needed:

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development`, `test`, or `production` |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins (comma-separated) |
| `DATABASE_URL` | `sqlite:///./data/resume_analyzer.db` | SQLAlchemy connection string (SQLite or PostgreSQL) |
| `MAX_UPLOAD_SIZE_MB` | `5` | Maximum PDF file upload size in megabytes |
| `MAX_JOB_DESCRIPTION_CHARS` | `20000` | Maximum characters accepted for job descriptions |
| `LLM_PROVIDER` | `auto` | `auto`, `mock`, `openai`, or `gemini` |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key (starts with `sk-...`) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API endpoint or compatible proxy |
| `GEMINI_API_KEY` | *(empty)* | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model name |

---

## AI Provider Configuration

The application features an automated, tiered fallback system:

1. **`LLM_PROVIDER=auto` (Default)**:
   - If `OPENAI_API_KEY` is present $\to$ Uses OpenAI (`gpt-4o-mini`).
   - Else if `GEMINI_API_KEY` is present $\to$ Uses Gemini (`gemini-1.5-flash`).
   - Otherwise $\to$ Gracefully falls back to the local **Mock Provider**.
2. **`LLM_PROVIDER=mock`**:
   - Runs a deterministic, offline heuristic engine based on regular expressions, skill catalogs, and text metrics.
   - Requires **no internet access and zero API keys**.
   - Generates fully populated, input-dependent reports with real skill matching and bullet rewrites.
3. **`LLM_PROVIDER=openai` / `LLM_PROVIDER=gemini`**:
   - Enforces structured JSON output matching the Pydantic `AnalysisResult` schema.
   - Includes automatic retry logic on malformed responses.

---

## Running Tests

### Backend Tests (pytest)
Runs 71 unit and integration tests covering PDF parsing, validation, error handling, repository operations, API endpoints, and LLM schemas:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

### Frontend Tests (Vitest)
Runs 23 component and unit tests covering validation, date and score formatting, `ScoreRing`, `AnalyzeForm`, and `HistoryList`:

```bash
cd frontend
npm test
```

### End-to-End Live Smoke Test
With both backend and frontend running:

```bash
.\backend\.venv\Scripts\python.exe verify_e2e_live.py
```

---

## API Documentation

FastAPI automatically generates interactive OpenAPI documentation:

- **Swagger UI**: [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **ReDoc**: [http://127.0.0.1:8000/api/redoc](http://127.0.0.1:8000/api/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/api/openapi.json](http://127.0.0.1:8000/api/openapi.json)

### Primary Endpoints

- `GET /api/health` — Service health, database status, and active LLM provider.
- `POST /api/analyze` — Multipart upload (`resume`: PDF file, `job_description`: string). Returns `201 Created` with full `AnalysisRecord`.
- `GET /api/analyses` — Paginated list of previous analyses (`limit`, `offset`).
- `GET /api/analyses/{id}` — Fetch a specific analysis record by UUID.
- `DELETE /api/analyses/{id}` — Delete an analysis record (`204 No Content`).

---

## Database & Migrations

The database layer utilizes SQLAlchemy 2.0 with a clean **Repository pattern**:
- Default: Embedded SQLite database stored in `backend/data/resume_analyzer.db`.
- **Migrating to PostgreSQL**:
  1. Install a Postgres driver: `pip install psycopg[binary]`.
  2. Change `DATABASE_URL` in `.env`:
     ```env
     DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/resume_analyzer
     ```
  3. No application code changes are required because all column types (`String`, `Integer`, `DateTime`, `JSON`) are fully portable across SQL dialects.

---

## Security & Privacy

- **Memory-Only Processing**: PDF files are read and processed entirely in memory via byte streams; no untrusted user files are stored on disk.
- **Content-Type & Magic Byte Verification**: Uploads are verified for `.pdf` extension, MIME types, and `%PDF-` magic header bytes to prevent malicious uploads.
- **Sanitized Filenames**: Paths and control characters are stripped from filenames (`sanitize_filename`) to prevent directory traversal attacks.
- **Privacy Preservation**: Raw resume text is **never stored** in the database. Only extracted metadata and the resulting structured score report are persisted.
- **Prompt Injection Defense**: Resume and job description texts are isolated in XML boundary tags `<resume>` and `<job_description>` with explicit instructions to ignore prompt overrides.
- **Credential Protection**: API keys are wrapped in Pydantic `SecretStr` so they are never exposed in log outputs or error messages.

---

## Known Limitations & Future Improvements

- **Scanned Image PDFs**: Resumes that are scans/images without an embedded text layer will be rejected with an actionable prompt to upload a text-based PDF. Future versions can incorporate OCR (e.g., Tesseract).
- **Multi-Resume Comparison**: Allowing users to compare multiple candidate resumes against a single job description side-by-side.
- **PDF Export of Analysis**: Generating an executive PDF report summarizing the ATS evaluation to share with career coaches.
- **Customizable Keyword Weights**: Giving users the ability to mark specific skills as "must-have" vs "nice-to-have".
