# Makefile for DFP Agent Orchestration

install:
	@echo "Installing dependencies..."
	uv sync --dev

run-local:
	powershell.exe -ExecutionPolicy Bypass -File .\run_locally.ps1
