#!/usr/bin/env bash
set -euo pipefail

echo "🐳 Luthier's Tool Box - Docker Compose Setup"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ Created .env file"
else
    echo "✓ .env file already exists"
fi

echo ""
echo "🏗️  Building containers..."
docker compose build

echo ""
echo "🚀 Starting containers..."
docker compose up -d

echo ""
echo "⏳ Waiting for API health check..."
for i in $(seq 1 30); do
    if curl -fsS http://localhost:${SERVER_PORT:-8000}/health >/dev/null 2>&1; then
        echo "✓ API is healthy!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "🎉 Stack is ready!"
echo ""
echo "📡 API:    http://localhost:${SERVER_PORT:-8000}"
echo "📡 Docs:   http://localhost:${SERVER_PORT:-8000}/docs"
echo "🌐 Client: http://localhost:${CLIENT_PORT:-8080}"
echo ""
echo "🧪 Test the API:"
echo "  curl http://localhost:${SERVER_PORT:-8000}/health"
echo ""
echo "🛑 Stop:"
echo "  docker compose down"
echo ""
echo "📊 View logs:"
echo "  docker compose logs -f"
