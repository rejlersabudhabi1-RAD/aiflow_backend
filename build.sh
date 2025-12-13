#!/bin/bash
# Railway build script - runs after files are copied
set -e

echo "🔧 Creating Python virtual environment..."
python -m venv /opt/venv

echo "📦 Upgrading pip..."
/opt/venv/bin/pip install --upgrade pip setuptools wheel

echo "📚 Installing dependencies from requirements.txt..."
/opt/venv/bin/pip install -r requirements.txt --no-cache-dir

echo "✅ Build complete!"
