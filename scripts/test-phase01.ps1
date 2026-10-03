param(
    [ValidateSet('before', 'baseline-green', 'after')]
    [string]$Stage = 'after',
    [string]$TestImage = 'sha256:dd640b49d87662da8e7b05ac08522d8f2bfc0579613a792d193f9685dd069edc',
    [string]$PlaywrightModule = $env:PLAYWRIGHT_MODULE
)
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$project = 'fluxio-phase01-tests'
$report = Join-Path $workspace 'results/phase01'
$e2eStarted = $false
New-Item -ItemType Directory -Force -Path $report | Out-Null
Push-Location $workspace
try {
    # This compose file has only movement_test and uses tmpfs, never the normal DB.
    & docker compose -p $project -f compose.test.yml up -d --wait db-test
    if ($LASTEXITCODE -ne 0) { throw 'Could not start disposable PostgreSQL' }
    & docker image inspect $TestImage --format '{{.Id}}' | Set-Content "$report/test-image.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Test image unavailable; build the test target first' }
    $testCommand = "python --version > results/phase01/python-runtime.txt; pip freeze > results/phase01/python-dependencies.txt; pytest -q > results/phase01/python-$Stage.log 2>&1; result=`$?; alembic current > results/phase01/alembic-$Stage.txt 2>&1; alembic heads >> results/phase01/alembic-$Stage.txt 2>&1; cat results/phase01/python-$Stage.log; exit `$result"
    & docker run --rm --network "${project}_default" `
        -e 'DATABASE_URL=postgresql+psycopg://movement:movement@db-test:5432/movement_test' `
        -e 'TEST_DATABASE_RESET=1' -e 'STORAGE_PATH=/tmp/fluxio-phase01-storage' `
        -v "${workspace}:/app" -w /app $TestImage sh -c $testCommand
    $pythonResult = $LASTEXITCODE
    if ($PlaywrightModule) { $env:PLAYWRIGHT_MODULE = $PlaywrightModule }
    & node --version | Set-Content "$report/node-runtime.txt"
    & node --test tests/*.test.cjs *> "$report/javascript-$Stage.log"
    $javascriptResult = $LASTEXITCODE
    Get-Content "$report/javascript-$Stage.log" -Tail 10
    if ($pythonResult -ne 0 -or $javascriptResult -ne 0) { throw "Failed: Python=$pythonResult JavaScript=$javascriptResult" }
    if ($Stage -eq 'after') {
        & docker run --rm -d --name fluxio-phase01-e2e --network "${project}_default" `
            -p '127.0.0.1:18769:8000' `
            -e 'DATABASE_URL=postgresql+psycopg://movement:movement@db-test:5432/movement_test' `
            -e 'TEST_DATABASE_RESET=1' -e 'PHASE01_E2E=1' `
            -e 'STORAGE_PATH=/tmp/fluxio-phase01-e2e' `
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
        & node tests/e2e/phase01.cjs *> "$report/e2e-after.log"
        $e2eResult = $LASTEXITCODE
        Get-Content "$report/e2e-after.log"
        if ($e2eResult -ne 0) { throw 'Live E2E failed' }
    }
} finally {
    if ($e2eStarted) {
        & docker logs fluxio-phase01-e2e *> "$report/e2e-server.log"
        & docker stop fluxio-phase01-e2e | Out-Null
    }
    & docker compose -p $project -f compose.test.yml down
    Pop-Location
}
