# Stage 1: Build & Prepare
FROM python:3.11-alpine AS builder

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache build-base

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-alpine

# Set work directory
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Run the FastAPI application using uvicorn (optimized for minimal footprint)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
