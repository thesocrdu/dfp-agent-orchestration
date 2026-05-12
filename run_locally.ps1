$ErrorActionPreference = 'Stop'

Write-Host "Stopping any existing processes on ports 8000-8003..."
Get-NetTCPConnection -LocalPort 8000, 8001, 8002, 8003 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }

$env:GOOGLE_CLOUD_PROJECT = (gcloud config get-value project 2>$null)
$env:GOOGLE_CLOUD_LOCATION = "us-central1"
$env:GOOGLE_GENAI_USE_VERTEXAI = "True"

Write-Host "Starting Developer Agent on port 8001..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd developer; `$env:APP_URL='http://localhost:8001'; uv run uvicorn app.server:app --host 0.0.0.0 --port 8001"

Write-Host "Starting I&T Engineer Agent on port 8002..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd it_engineer; `$env:APP_URL='http://localhost:8002'; uv run uvicorn app.server:app --host 0.0.0.0 --port 8002"

Write-Host "Starting QA Auditor Agent on port 8003..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd qa_auditor; `$env:APP_URL='http://localhost:8003'; uv run uvicorn app.server:app --host 0.0.0.0 --port 8003"

Start-Sleep -Seconds 5

Write-Host "Starting Orchestrator Agent on port 8000..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd orchestrator; `$env:APP_URL='http://localhost:8000'; `$env:DEVELOPER_AGENT_CARD_URL='http://localhost:8001/.well-known/agent.json'; `$env:IT_ENGINEER_AGENT_CARD_URL='http://localhost:8002/.well-known/agent.json'; `$env:QA_AUDITOR_AGENT_CARD_URL='http://localhost:8003/.well-known/agent.json'; uv run uvicorn app.server:app --host 0.0.0.0 --port 8000"

Write-Host "All agents started in separate windows!"
Write-Host "Orchestrator (Frontend): http://localhost:8000"
Write-Host "Developer: http://localhost:8001"
Write-Host "I&T Engineer: http://localhost:8002"
Write-Host "QA Auditor: http://localhost:8003"
