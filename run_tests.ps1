# PowerShell script to run tests with correct PYTHONPATH
$env:PYTHONPATH = "$(Resolve-Path .)"
pytest --cov=src --cov-report=term-missing
