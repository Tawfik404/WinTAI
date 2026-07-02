# WinTAI Development Setup Script
# Run from repository root

Write-Host "=== WinTAI Setup ===" -ForegroundColor Cyan

# Backend
Write-Host "`n[1/2] Setting up Python backend..." -ForegroundColor Yellow
Push-Location apps\backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
Pop-Location

# Frontend
Write-Host "`n[2/2] Installing frontend dependencies..." -ForegroundColor Yellow
Push-Location apps\frontend
npm install
Pop-Location

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Run backend:           cd apps\backend && python -m app.main"
Write-Host "Run frontend (browser): cd apps\frontend && npm run dev"
Write-Host "Run frontend (desktop): cd apps\frontend && npm run electron:dev"
