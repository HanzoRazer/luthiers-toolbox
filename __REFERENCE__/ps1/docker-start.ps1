# Luthier's Tool Box - Docker Compose Setup
Write-Host "🐳 Luthier's Tool Box - Docker Compose Setup" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host "📝 Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file" -ForegroundColor Green
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Load .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        Set-Item -Path "env:$name" -Value $value
    }
}

$SERVER_PORT = $env:SERVER_PORT
if (-Not $SERVER_PORT) { $SERVER_PORT = "8000" }
$CLIENT_PORT = $env:CLIENT_PORT
if (-Not $CLIENT_PORT) { $CLIENT_PORT = "8080" }

Write-Host ""
Write-Host "🏗️  Building containers..." -ForegroundColor Yellow
docker compose build

Write-Host ""
Write-Host "🚀 Starting containers..." -ForegroundColor Yellow
docker compose up -d

Write-Host ""
Write-Host "⏳ Waiting for API health check..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$healthy = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$SERVER_PORT/health" -TimeoutSec 1 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "`n✓ API is healthy!" -ForegroundColor Green
            $healthy = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline
    }
    $attempt++
    Start-Sleep -Seconds 1
}

if (-Not $healthy) {
    Write-Host "`n❌ API health check timed out" -ForegroundColor Red
    Write-Host "Check logs: docker compose logs api" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🎉 Stack is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📡 API:    http://localhost:$SERVER_PORT" -ForegroundColor Cyan
Write-Host "📡 Docs:   http://localhost:$SERVER_PORT/docs" -ForegroundColor Cyan
Write-Host "🌐 Client: http://localhost:$CLIENT_PORT" -ForegroundColor Cyan
Write-Host ""
Write-Host "🧪 Test the API:" -ForegroundColor Yellow
Write-Host "  curl http://localhost:$SERVER_PORT/health" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 Stop:" -ForegroundColor Yellow
Write-Host "  docker compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "📊 View logs:" -ForegroundColor Yellow
Write-Host "  docker compose logs -f" -ForegroundColor Gray
