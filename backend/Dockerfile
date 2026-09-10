FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  gcc \
  g++ \
  make \
  swig \
  libgl1 \
  libglib2.0-0 \
  libpq-dev \
  curl \
  ffmpeg \
&& rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt
RUN pip install psycopg2-binary

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs /data/evidence

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "run.py"]
