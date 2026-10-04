param(
    [string]$TestImage = 'fluxio-whatsapp-tests:phase2',
    [string]$PlaywrightModule = 'C:/Users/desarrollo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright',
    [string]$PublicBaseUrl,
    [string]$ReportDirectory = 'results/releases/weekly-sharing-20261004',
    [switch]$E2EOnly
)
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$project = 'fluxio-weekly-release'
$server = 'fluxio-weekly-release-e2e'
$serverStarted = $false
Push-Location $workspace
try {
    if (-not $PublicBaseUrl) {
        $setting = Select-String -LiteralPath '.env' -Pattern '^PUBLIC_BASE_URL=' | Select-Object -First 1
        if ($setting) { $PublicBaseUrl = $setting.Line.Substring('PUBLIC_BASE_URL='.Length).Trim() }
    }
    $publicUri = $null
    if (-not [Uri]::TryCreate($PublicBaseUrl, [UriKind]::Absolute, [ref]$publicUri) -or $publicUri.Scheme -ne 'https' -or $publicUri.UserInfo -or $publicUri.Query -or $publicUri.Fragment) {
        throw 'Supply the actual HTTPS PUBLIC_BASE_URL using -PublicBaseUrl or the local .env setting'
    }
    New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null
    $env:PLAYWRIGHT_MODULE = $PlaywrightModule
    $productionFiles = @(rg --files app migrations)
    $before = @{}
    foreach ($item in $productionFiles) { $before[$item] = (Get-FileHash -LiteralPath $item -Algorithm SHA256).Hash }
    $before | ConvertTo-Json | Set-Content "$ReportDirectory/source-before.json"
    & docker image inspect $TestImage --format '{{.Id}}' *> "$ReportDirectory/test-image.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Existing test image unavailable' }
    & docker compose -p $project -f compose.test.yml up -d --wait db-test
    if ($LASTEXITCODE -ne 0) { throw 'Disposable database startup failed' }
    $arguments = @('run','--rm','--network',"${project}_default",
        '-e','DATABASE_URL=postgresql+psycopg://movement:movement@db-test:5432/movement_test',
        '-e','TEST_DATABASE_RESET=1','-e','STORAGE_PATH=/tmp/weekly-release-tests',
        '-e',"WEEKLY_RELEASE_PUBLIC_BASE_URL=$PublicBaseUrl",
        '-e',"WEEKLY_RELEASE_REPORT_DIR=$ReportDirectory",
        '-v',"${workspace}:/app",'-w','/app',$TestImage)
    & docker @arguments pytest -q tests/test_weekly_release_validation.py tests/test_weekly_summary.py *> "$ReportDirectory/python-targeted.log"
    Get-Content "$ReportDirectory/python-targeted.log"
    if ($LASTEXITCODE -ne 0) { throw 'Targeted release gate failed' }
    if (-not $E2EOnly) {
    & docker @arguments pytest -q *> "$ReportDirectory/python-full.log"
    Get-Content "$ReportDirectory/python-full.log"
    if ($LASTEXITCODE -ne 0) { throw 'Full Python gate failed' }
    & node --test tests/*.test.cjs *> "$ReportDirectory/javascript-full.log"
    if ($LASTEXITCODE -ne 0) { throw 'Full JavaScript gate failed' }
    & node --test tests/athlete-integration.test.cjs tests/athlete-state.test.cjs *> "$ReportDirectory/athlete-ux.log"
    if ($LASTEXITCODE -ne 0) { throw 'Athlete UX gate failed' }
    & node --test tests/review-state.test.cjs tests/studio-integration.test.cjs *> "$ReportDirectory/coach-ux.log"
    if ($LASTEXITCODE -ne 0) { throw 'Coach UX gate failed' }
    & node --test tests/training-ux.test.cjs *> "$ReportDirectory/bitacora-ux.log"
    if ($LASTEXITCODE -ne 0) { throw 'Bitacora UX gate failed' }
    }
    & docker @arguments alembic current *> "$ReportDirectory/alembic-current.log"
    if ($LASTEXITCODE -ne 0) { throw 'Alembic head check failed' }
    & docker run --rm -d --name $server --network "${project}_default" -p '127.0.0.1:18771:8000' `
        -e 'DATABASE_URL=postgresql+psycopg://movement:movement@db-test:5432/movement_test' `
        -e 'TEST_DATABASE_RESET=1' -e 'PHASE01_E2E=1' -e 'STORAGE_PATH=/tmp/weekly-release-e2e' `
        -v "${workspace}:/app" -w /app $TestImage uvicorn tests.e2e.app:app --host 0.0.0.0 --port 8000
    if ($LASTEXITCODE -ne 0) { throw 'Isolated E2E server failed' }
    $serverStarted = $true
    function Wait-ReleaseServer {
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            & docker exec $server python -c "import json; from urllib.request import urlopen; assert json.load(urlopen('http://127.0.0.1:8000/health', timeout=1))['ok'] is True" *> "$ReportDirectory/e2e-health.log"
            if ($LASTEXITCODE -eq 0) { return }
            Start-Sleep -Seconds 1
        }
        throw 'Isolated E2E health timeout'
    }
    Wait-ReleaseServer
    $env:PHASE01_E2E_URL = 'http://localhost:18771'
    & node tests/e2e/phase01.cjs *> "$ReportDirectory/athlete-coach-bitacora-e2e.log"
    if ($LASTEXITCODE -ne 0) { throw 'Athlete/Coach/Bitacora E2E failed' }
    & docker restart $server | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Fixture reset failed' }
    Wait-ReleaseServer
    $env:WEEKLY_E2E_URL = 'http://localhost:18771'
    & node tests/e2e/weekly.cjs *> "$ReportDirectory/weekly-sharing-e2e.log"
    if ($LASTEXITCODE -ne 0) { throw 'Weekly/sharing E2E failed' }
    $unchanged = @($productionFiles | Where-Object { (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash -ne $before[$_] })
    if ($unchanged.Count) { throw "Production source changed during validation: $unchanged" }
    @{production_files_verified=$productionFiles.Count; production_source_unchanged=$true; real_public_base_url=$PublicBaseUrl; deployed=$false; e2e_only_recovery=[bool]$E2EOnly} |
        ConvertTo-Json | Set-Content "$ReportDirectory/summary.json"
    Write-Output "All release gates passed. Evidence: $ReportDirectory"
} finally {
    if ($serverStarted) {
        & docker logs $server *> "$ReportDirectory/e2e-server.log"
        & docker stop $server | Out-Null
    }
    & docker compose -p $project -f compose.test.yml down
    Pop-Location
}
