#!/usr/bin/env pwsh
# Refresh environment variables and start the API
Refresh-EnvironmentVariables.ps1
$env:PYTHONPATH = "."
uv run python app/run.py 