# Quick test runner for Dream.OS development
# Runs unit tests with coverage and parallel execution

$ErrorActionPreference = "Stop"

# Get the root directory
$rootDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# Activate virtual environment if it exists
$venvPath = Join-Path $rootDir "venv"
if (Test-Path $venvPath) {
    Write-Host "🔧 Activating virtual environment..."
    & "$venvPath\Scripts\Activate.ps1"
}

# Run tests
Write-Host "🧪 Running quick test suite..."
python "$rootDir\run_tests.py" `
    --category unit `
    --coverage `
    --parallel `
    --verbose

# Check if tests passed
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Tests failed!" -ForegroundColor Red
    exit 1
} 