# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim
WORKDIR /app

# Create non-root user
RUN groupadd -r guineecare && useradd -r -g guineecare -d /app -s /sbin/nologin guineecare

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Set ownership
RUN chown -R guineecare:guineecare /app

# Switch to non-root user
USER guineecare

EXPOSE 8000

# Use gunicorn with uvicorn workers for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
