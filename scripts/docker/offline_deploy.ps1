param(
    [string]$ArchivePath = "runtime/offline/acslagent-unified_offline.tar",
    [string]$ComposeFile = "docker-compose.unified.offline.yml",
    [switch]$SkipChecksum
)

$ErrorActionPreference = "Stop"

function Assert-Command([string]$CommandName) {
    if (-not (Get-Command $CommandName -ErrorAction SilentlyContinue)) {
        throw "Missing command: $CommandName"
    }
}

Assert-Command "docker"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

if (-not (Test-Path $ArchivePath)) {
    throw "Archive not found: $ArchivePath"
}
if (-not (Test-Path $ComposeFile)) {
    throw "Compose file not found: $ComposeFile"
}
if (-not (Test-Path ".env")) {
    throw "Missing .env. Run: Copy-Item .env.example .env"
}

$shaPath = "$ArchivePath.sha256.txt"
if ((-not $SkipChecksum) -and (Test-Path $shaPath)) {
    Write-Host "[0/4] Verifying archive checksum..."
    $expectedLine = (Get-Content $shaPath -ErrorAction Stop | Select-Object -First 1).Trim()
    if (-not $expectedLine) {
        throw "Checksum file is empty: $shaPath"
    }
    $expectedHash = ($expectedLine -split "\s+")[0].ToUpperInvariant()
    $actualHash = (Get-FileHash -Algorithm SHA256 -Path $ArchivePath).Hash.ToUpperInvariant()
    if ($expectedHash -ne $actualHash) {
        throw "Checksum mismatch for archive: $ArchivePath"
    }
}

Write-Host "[1/4] Loading offline image archive..."
docker load -i $ArchivePath
if ($LASTEXITCODE -ne 0) {
    throw "docker load failed"
}

Write-Host "[2/4] Starting unified offline service..."
docker compose -f $ComposeFile up -d
if ($LASTEXITCODE -ne 0) {
    throw "docker compose up failed"
}

Write-Host "[3/4] Waiting for health endpoint..."
$healthy = $false
for ($i = 1; $i -le 12; $i++) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    } catch {
    }
    Start-Sleep -Seconds 2
}

Write-Host "[4/4] Health check result..."
if ($healthy) {
    Write-Host "Health check status code: 200"
} else {
    Write-Warning "Service started but health endpoint is not ready yet."
}

Write-Host "Offline deployment finished."
