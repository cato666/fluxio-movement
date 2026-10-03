param(
    [string]$TestImage = 'fluxio-whatsapp-tests:phase2',
    [string]$PlaywrightModule = $env:PLAYWRIGHT_MODULE
)
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runName = Get-Date -Format 'yyyyMMdd-HHmmss'
$project = "fluxio-whatsapp-check-$runName"
$container = "$project-e2e"
$relativeReport = "results/whatsapp/reproduction-$runName"
$report = Join-Path $workspace $relativeReport
$e2eStarted = $false
New-Item -ItemType Directory -Force -Path $report | Out-Null
Push-Location $workspace
try {
    # No env-file, normal DB, named DB volume, host DB port or real credentials.
    & docker image inspect $TestImage --format '{{.Id}}' | Set-Content "$report/test-image.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Build Dockerfile target test first, or supply an available test image' }
    & docker compose -p $project -f compose.test.yml up -d --wait db-test
    if ($LASTEXITCODE -ne 0) { throw 'Could not start disposable PostgreSQL' }
    $testCommand = "pytest -q > $relativeReport/python.log 2>&1; result=`$?; cat $relativeReport/python.log; exit `$result"
    & docker run --rm --network "${project}_default" `
        -e 'DATABASE_URL=postgresql+psycopg://movement:movement@db-test:5432/movement_test' `
        -e 'TEST_DATABASE_RESET=1' -e 'STORAGE_PATH=/tmp/fluxio-whatsapp-storage' `
        -v "${workspace}:/app" -w /app $TestImage sh -c $testCommand
    if ($LASTEXITCODE -ne 0) { throw 'Python gate failed; stopping' }
    if ($PlaywrightModule) { $env:PLAYWRIGHT_MODULE = $PlaywrightModule }
    & node --test tests/*.test.cjs *> "$report/javascript.log"
    if ($LASTEXITCODE -ne 0) { throw 'JavaScript gate failed; stopping' }
    & docker run --rm --network "${project}_default" `
        -e 'DATABASE_URL=postgresql+psycopg://movement:movement@db-test:5432/movement_test' `
        -v "${workspace}:/app" -w /app $TestImage alembic current *> "$report/alembic.log"
    if ($LASTEXITCODE -ne 0) { throw 'Alembic check failed' }
    & docker run --rm -d --name $container --network "${project}_default" `
        -p '127.0.0.1:18769:8000' `
        -e 'DATABASE_URL=postgresql+psycopg://movement:movement@db-test:5432/movement_test' `
        -e 'TEST_DATABASE_RESET=1' -e 'PHASE01_E2E=1' `
        -e 'STORAGE_PATH=/tmp/fluxio-whatsapp-e2e' `
        -v "${workspace}:/app" -w /app $TestImage `
        uvicorn tests.e2e.app:app --host 0.0.0.0 --port 8000
    if ($LASTEXITCODE -ne 0) { throw 'Could not start isolated E2E server' }
    $e2eStarted = $true
    $ready = $false
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        try {
            $response = Invoke-WebRequest 'http://localhost:18769/health' -TimeoutSec 1
            if ($response.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw 'Isolated E2E server did not become healthy' }
    $env:PHASE01_E2E_URL = 'http://localhost:18769'
    & node tests/e2e/phase01.cjs *> "$report/e2e.log"
    Get-Content "$report/e2e.log"
    if ($LASTEXITCODE -ne 0) { throw 'E2E gate failed; stopping' }
    Write-Output "All gates passed. Evidence: $report"
} finally {
    if ($e2eStarted) {
        & docker logs $container *> "$report/e2e-server.log"
        & docker stop $container | Out-Null
    }
    & docker compose -p $project -f compose.test.yml down
    Pop-Location
}
