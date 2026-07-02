# Start both backend and frontend in parallel
# Requires two terminal windows

Write-Host "=== WinTAI Development ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Terminal 1 (Backend):"
Write-Host "  cd apps\backend"
Write-Host "  .\.venv\Scripts\activate"
Write-Host "  python -m app.main"
Write-Host ""
Write-Host "Terminal 2 (Frontend - browser):"
Write-Host "  cd apps\frontend"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Terminal 2 (Frontend - desktop app):"
Write-Host "  cd apps\frontend"
Write-Host "  npm run electron:dev"
Write-Host ""
Write-Host "Frontend (browser): http://localhost:5173"
Write-Host "Backend:            http://127.0.0.1:8000"
Write-Host "API docs:           http://127.0.0.1:8000/docs"
