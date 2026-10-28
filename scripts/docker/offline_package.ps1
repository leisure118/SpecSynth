param(
    [string]$ImageTag = "acslagent-unified:offline",
    [string]$BaseImage = "python:3.13-slim",
    [string]$AptMirror = "",
    [string]$PipIndexUrl = "",
    [string]$PipExtraIndexUrl = "",
    [string]$NpmRegistry = "",
    [string]$HttpProxy = "",
    [string]$HttpsProxy = "",
    [string]$NoProxy = "",
    [string]$OutputDir = "runtime/offline",
    [switch]$SkipBuild
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

$outputPath = Join-Path $repoRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputPath | Out-Null

if (-not $SkipBuild) {
    Write-Host "[1/4] Building unified image..."
    $composeArgs = @(
        "compose", "-f", "docker-compose.unified.yml", "build",
        "--build-arg", "BASE_IMAGE=$BaseImage",
        "--build-arg", "APT_MIRROR=$AptMirror",
        "--build-arg", "PIP_INDEX_URL=$PipIndexUrl",
        "--build-arg", "PIP_EXTRA_INDEX_URL=$PipExtraIndexUrl",
        "--build-arg", "NPM_REGISTRY=$NpmRegistry",
        "--build-arg", "HTTP_PROXY=$HttpProxy",
        "--build-arg", "HTTPS_PROXY=$HttpsProxy",
        "--build-arg", "NO_PROXY=$NoProxy"
    )
    & docker @composeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose build failed"
    }

    Write-Host "[2/4] Tagging unified image for offline deployment..."
    docker image tag acslagent-unified:latest $ImageTag
    if ($LASTEXITCODE -ne 0) {
        throw "docker image tag failed"
    }
}

Write-Host "[3/4] Validating image exists..."
docker image inspect $ImageTag | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Image not found: $ImageTag"
}

$tarName = ($ImageTag -replace "[:/]", "_") + ".tar"
$tarPath = Join-Path $outputPath $tarName
$shaPath = "$tarPath.sha256.txt"

Write-Host "[4/4] Saving image archive to $tarPath ..."
docker save -o $tarPath $ImageTag
if ($LASTEXITCODE -ne 0) {
    throw "docker save failed"
}

$hash = Get-FileHash -Algorithm SHA256 -Path $tarPath
"$($hash.Hash)  $tarName" | Set-Content -Encoding ascii -Path $shaPath

Write-Host "Offline package ready:"
Write-Host "- Tar: $tarPath"
Write-Host "- SHA256: $shaPath"
Write-Host "Use scripts/docker/offline_deploy.ps1 on the target machine."
