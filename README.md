# Enterprise AI Data Automation Pipeline

- An opinionated FastAPI-based pipeline that ingests a document image/PDF plus a ledger spreadsheet, creates a tracking row in Postgres, and dispatches an asynchronous Celery worker to extract, enrich (OCR / web-scrape / LLM), and store structured results. Intended for teams building real-time, multi-source document extraction & reconciliation (local upload → background processing → queryable job status).

# Stack

- Language(s): Python (primary), Dockerfile (runtime packaging)
- Framework / runtime: FastAPI + Uvicorn; Celery workers for background processing
- Notable libraries: FastAPI, SQLAlchemy, Celery, Playwright, OpenAI (plus pandas / openpyxl / boto3)

# Stucture Tree View

Dockerfile                 # production image (installs Playwright browsers)
docker-compose.yml         # orchestration for app + workers/broker/db (present)
requirements.txt           # pinned Python deps (FastAPI, Celery, SQLAlchemy, Playwright, OpenAI, ...)
README.md                  # project overview + architecture notes
app/
  __init__.py
  config.py                # pydantic Settings (env-driven: DATABASE_URL, AWS, OPENAI, proxies, etc.)
  database.py              # DB engine / Base / get_db (Postgres)
  main.py                  # FastAPI app, endpoints: POST /api/v1/automation/process, GET /api/v1/automation/status/{job_id}
  models.py                # AutomationJob, JobStatus (DB models)
  schemas.py               # Pydantic response/request models (JobResponse, JobStatusResponse)
  core/
    excel_parser.py        # spreadsheet parsing / validation
    ocr_engine.py          # OCR / handwritten form extraction
    web_scrapper.py        # Playwright-based scraping for target_url
    llm_aggregator.py      # orchestration of LLM calls / consolidation
  workers/
    celery_app.py          # Celery app factory / config
    tasks.py               # process_pipeline_worker Celery task (queues the extraction pipeline)
tests/                     # test suite (pytest)

# How to run it

Quick checklist (prereqs)

Install: Git, Python 3.10+ (or your project's target), pip, Docker & docker-compose (if using Docker).
Install Redis and Postgres locally or plan to use the docker-compose services.
Obtain external creds: AWS (Textract), OpenAI API key, Bright Data proxy creds.
A. Clone the repo

git clone https://github.com/JayNguyen-123/AI_DATA_AUTOMATION.git
cd AI_DATA_AUTOMATION

B. Recommended: Run with Docker Compose (fast start)

1. Create a .env file at repo root (see template below).
2. Build & start:
    docker-compose up -d --build
3. Watch logs:
    docker-compose logs -f app # FastAPI service
    docker-compose logs -f worker # Celery worker
   
C. Local development (without Docker)

1. Create & activate a virtualenv
    python -m venv .venv
    source .venv/bin/activate (macOS/Linux) or .venv\Scripts\activate (Windows)
2. Install dependencies
    pip install -r requirements.txt
3. Start required infra (Redis + Postgres). Quick Docker commands:
    docker run -d --name redis -p 6379:6379 redis
    docker run -d --name pg -e POSTGRES_PASSWORD=pass -e POSTGRES_USER=user -e POSTGRES_DB=ai_data -p    5432:5432 postgres:15 Or use your local/Postgres service.
4. Populate environment variables (see template below) — either export them in your shell or create a .env and use python-dotenv if app loads it.
5. Initialize DB schema
  - If the repo uses Alembic: alembic upgrade head
  - If not: run SQLAlchemy create_all (one-off):
      python - <<'PY' from app.database import Base, engine      Base.metadata.create_all(bind=engine)      PY
6. Start the Celery worker
  - celery -A app.workers.celery_app worker --loglevel=info (If the celery object is named differently, adapt the -A path accordingly, e.g., app.workers.celery_app:celery)
7. Start the FastAPI app (dev)
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
8. Visit http://localhost:8000 (or the configured port). Check OpenAPI at /docs if available.

Example .env template (fill values) DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/ai_data 
REDIS_URL=redis://localhost:6379/0 
CELERY_BROKER_URL=${REDIS_URL} 
CELERY_RESULT_BACKEND=${REDIS_URL} 
AWS_ACCESS_KEY_ID= 
AWS_SECRET_ACCESS_KEY= 
AWS_REGION=us-east-1 
OPENAI_API_KEY= 
BRIGHTDATA_USERNAME= 
BRIGHTDATA_PASSWORD= 
BRIGHTDATA_PROXY_HOST=proxy.brightdata.com 
BRIGHTDATA_PROXY_PORT=22225 
SECRET_KEY=change-me 
ENV=development 
LOG_LEVEL=INFO

# Quick smoke test (example)

Find the upload endpoint in app/main.py or routers (common names: /upload, /documents). Example curl (adjust path): 
    curl -F "file=@/path/to/doc.pdf" http://localhost:8000/upload

Troubleshooting tips

  - “Connection refused” for Redis/Postgres: ensure services are running and the host/port in .env match.
  - Celery tasks not processed: confirm worker is running and that CELERY_BROKER_URL matches Redis; inspect worker logs.
  - Missing tables: run migrations or the create_all command above.
  - Secrets/keys: ensure OPENAI_API_KEY and AWS credentials are set; check provider quotas and network access.
  - Use docker-compose logs -f service to tail logs and find tracebacks.



