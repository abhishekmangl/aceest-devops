# ── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

# Prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies into an isolated prefix so they can be copied cleanly
COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

# Create a non-root user for security
RUN addgroup --system aceest && adduser --system --ingroup aceest aceest

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app.py .
COPY requirements.txt .

# Change ownership to non-root user
RUN chown -R aceest:aceest /app

USER aceest

EXPOSE 5000

# Use exec form so signals reach Flask directly
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
