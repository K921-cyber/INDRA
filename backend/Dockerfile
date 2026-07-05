
# ==================== Build Stage ====================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system deps needed for psycopg2 / asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (system-wide install for multi-stage copy)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==================== Runtime Stage ====================
FROM python:3.11-slim

WORKDIR /app

# Install runtime system deps (just curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder to system-wide locations
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --shell /bin/sh appuser && \
    chown -R appuser:appgroup /app

# Switch to non-root user for security
USER appuser

# Expose port
EXPOSE 8000

# Default command (overridden by docker-compose override for dev with --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

