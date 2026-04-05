$ErrorActionPreference = "Stop"

Write-Host "=== KubeInsights Live Cluster Test Setup ===" -ForegroundColor Cyan

# 1. Setup Pytest
Write-Host "Installing/Verifying Python dependencies (pytest)..." -ForegroundColor Yellow
pip install pytest
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install pytest." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Verify/Install Kind
$kindInstalled = Get-Command kind -ErrorAction SilentlyContinue
if (-not $kindInstalled) {
    Write-Host "Kind is not installed. Attempting to install via winget..." -ForegroundColor Yellow
    winget install -e --id Kubernetes.kind --accept-source-agreements --accept-package-agreements
    
    # Reload environment block for current process so we can use kind immediately
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "Command 'kind' is available." -ForegroundColor Green
}

# Ensure Docker is running (Basic check)
$dockerRunning = Get-Process "Docker Desktop", "dockerd", "com.docker.backend" -ErrorAction SilentlyContinue
if (-not $dockerRunning) {
    Write-Host "WARNING: Docker Engine/Desktop process not found. 'kind' requires Docker to be running!" -ForegroundColor Red
    Write-Host "Please start Docker and run this script again." -ForegroundColor Yellow
    # Give a small warning but don't hard exit just in case process name differs (e.g., WSL2 backends)
}

# 3. Create Cluster
Write-Host "`n=== Spinning up local Kind cluster ===" -ForegroundColor Cyan
# Suppress error if the cluster already exists, just recreate or re-use it
$clusters = @()
try {
    $clusters = (kind get clusters 2>$null)
} catch {
    # It's expected to throw an error if no clusters exist
}

if ($clusters -contains "ingestion-test") {
    Write-Host "Cluster 'ingestion-test' already exists. We will reuse it." -ForegroundColor Yellow
} else {
    kind create cluster --name ingestion-test
}

try {
    # 4. Apply Test Resources
    Write-Host "`n=== Applying Test Kubernetes Resources ===" -ForegroundColor Cyan
    kubectl apply -f "$PSScriptRoot\tests\test_resources.yaml"
    
    Write-Host "Waiting for test-pod to be ready (this can take ~30-60s during first image pull)..." -ForegroundColor Yellow
    kubectl wait --for=condition=ready pod/test-pod -n ingestion-test-ns --timeout=120s
    
    # 5. Run Ingestion Tests
    Write-Host "`n=== Running Ingestion Pytest ===" -ForegroundColor Cyan
    Set-Location $PSScriptRoot
    # Using python -m pytest to ensure it runs out of current environment
    python -m pytest tests/test_live_ingest.py -v
    
    Write-Host "`n=== Test Run Completed Successfully! ===" -ForegroundColor Green

} finally {
    # 6. Teardown Cluster
    Write-Host "`n=== Tearing down Kind cluster ===" -ForegroundColor Cyan
    kind delete cluster --name ingestion-test
}
