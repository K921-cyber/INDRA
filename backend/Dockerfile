# ==================== Build Stage ====================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system deps needed for psycopg2 / asyncpg / bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (system-wide install for multi-stage copy)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ==================== Runtime Stage ====================
FROM python:3.11-slim

WORKDIR /app

# Install runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libffi8 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder to system-wide locations
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Ensure bcrypt is available (multi-stage copy can miss compiled extensions)
RUN pip install --no-cache-dir bcrypt>=4.0.1

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --shell /bin/sh appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app

# Switch to non-root user for security
USER appuser

# Expose port
EXPOSE 8000

# Default command (overridden by docker-compose override for dev with --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
