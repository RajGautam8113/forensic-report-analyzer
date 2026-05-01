FROM python:3.11-slim

# Install Tesseract OCR only (opencv-python-headless needs no system deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy project
COPY . .

# Create directories
RUN mkdir -p app/uploads app/data uploads data

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080

WORKDIR /app/app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "--workers", "1", "--threads", "2", "main:app"]
