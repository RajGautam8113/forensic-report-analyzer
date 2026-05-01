#!/usr/bin/env bash
# Render build script

set -o errexit

# Install CPU-only PyTorch (saves ~1.5GB vs GPU version)
pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install all other dependencies
pip install --no-cache-dir -r requirements.txt

# Download spaCy language model
python -m spacy download en_core_web_sm

# Create necessary directories
mkdir -p app/uploads app/data
