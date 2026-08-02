# Plan: Docker/CI + Deployment (Issue #9)

**Date**: 2026-08-02
**Branch**: `prod/deploy`
**Base**: `main` (8f98a9a + PR #16 merged)

## Goal
One-command containerized deployment of the FastAPI gateway + Celery worker on a free tier, with CI gates and env validation at startup.

## Steps

### 1. Pydantic Settings env validation on startup
- Add `pydantic-settings` to requirements.txt.
- Add a `validate_startup()` in `settings.py` that uses a pydantic `BaseSettings` subclass to:
  - Parse the full env schema (WHATSAPP_*, GROQ_API_KEY, BROKER_URL, DATABASE_URL, etc.).
  - **Fail fast (exit 1)** on startup if a *required* var is missing in production.
  - Optional vars get sane defaults (existing behavior preserved).
- Wire into `main.py` startup via FastAPI lifespan so both `uvicorn main:app` and Celery worker fail early and loudly.
- Keep the existing lazy `Settings` properties (tests monkeypatch env after import; do NOT break that).

### 2. Docker
- Multi-stage `Dockerfile` in `ai-service/`:
  - Build stage: install from requirements.
  - Runtime stage: same image used for both processes, controlled by CMD/entrypoint:
    - default `CMD` → `uvicorn main:app --host 0.0.0.0 --port 8000`
    - `worker` arg → `celery -A worker.celery_app worker --loglevel=info`
- `.dockerignore` (venv, __pycache__, .env, tests maybe keep for CI).
- Include `docs/` not needed in image.

### 3. GitHub Actions CI
- `.github/workflows/ci.yml`:
  - `test` job on ubuntu-latest: setup python 3.12, `pip install -r requirements.txt`, run `pytest -q`.
  - `docker` job: build image to ensure Dockerfile is valid.
- Uses a plain requirements install (no external services needed — suite uses sqlite/`CELERY_TASK_ALWAYS_EAGER`).

### 4. Deployment config
- `railway.json` + `Procfile` (worker + web) for Railway free tier; or Render blueprint `render.yaml`.
- Document env vars required in production in `.env.example` (already largely present).
- Add `DOCKERFILE` reference in railway config so platform builds the image.

## Definition of Done
- `docker build` succeeds locally.
- `pytest -q` still green (all ~76 tests).
- CI workflow file passes `yaml` parse; github action present.
- Deployment manifest (railway.json / render.yaml / Procfile) present.
