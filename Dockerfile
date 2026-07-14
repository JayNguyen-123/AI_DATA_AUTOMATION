# Docker file
# ========================================================
# Stage 1: Build dependencies and copy system components
# ========================================================
FROM python:3.11-slim AS builder

WORKDIR /workspace

# Install essential system tools required for compilation layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /lib/apt/lists/*

# Install python execution layers directly to a clean workspace path
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ========================================================
# Stage 2: Final Production Minimalistic Container Image
# ========================================================
FROM python:3.11-slim

WORKDIR /app

# Install lightweight runtime requirements for Postgres and browser mechanics
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Fetch built packages from the builder stage
COPY --from=builder /install /usr/local
COPY . .

# Download the sandboxed Playwright Chromium dependencies securely
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Create local system directories for multi-file transfers
RUN mkdir -p /tmp/automation_uploads && chmod 777 /tmp/automation_uploads

# Default execution pattern is overwritten inside docker-compose for workers
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
