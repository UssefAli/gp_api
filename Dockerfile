FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
RUN pip install --upgrade pip && pip install .

# Copy project
COPY . .

# Render listens on port 10000
EXPOSE 10000

# Start FastAPI (IMPORTANT PART)
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "10000"]
