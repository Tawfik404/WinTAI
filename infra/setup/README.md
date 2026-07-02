# WinTAI Setup

## Prerequisites

- Python 3.12+
- Node.js 22+
- npm 10+
- Windows 10/11

## Quick Start

```powershell
# From repository root
powershell -ExecutionPolicy Bypass -File infra\scripts\setup.ps1
```

## Manual Setup

### Backend
```powershell
cd apps\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend
```powershell
cd apps\frontend
npm install
```

## Development

See `infra\scripts\dev.ps1` for run instructions.
