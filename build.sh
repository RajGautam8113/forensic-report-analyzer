#!/usr/bin/env bash
# Render build script

set -o errexit

# Install Tesseract OCR (system dependency for pytesseract)
apt-get update && apt-get install -y --no-install-recommends tesseract-ocr && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
pip install --no-cache-dir -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Create necessary directories
mkdir -p app/uploads app/data
