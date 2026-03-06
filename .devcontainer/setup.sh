#!/bin/bash
set -e

echo "🔧 Setting up Production Shop Codespace..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update -y

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get install -y \
  build-essential \
  curl \
  git \
  jq \
  libpq-dev \
  sqlite3

# Python backend setup
echo "🐍 Setting up Python backend..."
cd services/api
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-cov black pylint

# Frontend setup
echo "🎨 Setting up Vue 3 frontend..."
cd ../../packages/client
npm install

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p ../../data
mkdir -p ../../logs
mkdir -p ../../cbsp21/full_source
mkdir -p ../../cbsp21/scanned_source

# Initialize database
echo "🗄️  Initializing databases..."
touch /tmp/art_studio.db
chmod 666 /tmp/art_studio.db

# Verify fence system
echo "🔒 Verifying fence system..."
cd ../..
if [ -f "FENCE_REGISTRY.json" ]; then
  echo "✅ FENCE_REGISTRY.json found"
  python -m json.tool FENCE_REGISTRY.json > /dev/null && echo "✅ Valid JSON" || echo "⚠️  Invalid JSON"
fi

# Make CI scripts executable
echo "🔐 Making CI scripts executable..."
chmod +x scripts/ci/*.py
chmod +x scripts/ci/check_art_studio_scope.py
chmod +x services/api/app/ci/fence_runner.py

# Test fence runner
echo "🧪 Testing fence runner..."
cd services/api
python -m app.ci.fence_runner --list || echo "⚠️  Fence runner not yet functional"

# Git configuration for Codespaces
echo "🔧 Configuring Git for Codespaces..."
git config --global --add safe.directory /workspace/luthiers-toolbox

echo ""
echo "✅ Codespace setup complete!"
echo ""
echo "📝 Quick Start Commands:"
echo "  make start-api     # Start FastAPI backend (port 8000)"
echo "  make start-client  # Start Vite frontend (port 5173)"
echo "  make check-boundaries  # Run all fence checks"
echo ""
echo "🔒 Fence System:"
echo "  python -m app.ci.fence_runner --list  # List all fences"
echo "  make check-boundaries                 # Run all checks"
echo ""
echo "🧪 Testing:"
echo "  cd services/api && pytest tests/ -v   # Run backend tests"
echo "  cd packages/client && npm run test    # Run frontend tests"
echo ""
