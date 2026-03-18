FROM python:3.11-slim

LABEL maintainer="medical-coding-system"
LABEL description="AI-assisted ICD-10/CPT clinical coding pipeline"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY data/ ./data/
COPY main.py .
COPY generate_pdf.py .

# Create writable directories
RUN mkdir -p /app/logs /app/output

# Default environment
ENV LOG_LEVEL=INFO
ENV LOG_DIR=/app/logs

# Entrypoint: run the CLI
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
