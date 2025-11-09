#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Luthier's Tool Box - Monorepo Quick Start"
echo ""

# Check if we're in the right directory
if [ ! -f "pnpm-workspace.yaml" ]; then
    echo "❌ Error: pnpm-workspace.yaml not found"
    echo "Please run this script from the repository root"
    exit 1
fi

echo "📦 Step 1: Installing API dependencies..."
cd services/api

if [ ! -d ".venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv .venv
fi

echo "   Activating virtual environment..."
source .venv/bin/activate

echo "   Installing requirements..."
pip install -q -r requirements.txt

echo ""
echo "✓ API dependencies installed"
echo ""
echo "🎯 Step 2: Starting API server..."
echo "   Server will run at: http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop"
echo ""

uvicorn app.main:app --reload --port 8000
