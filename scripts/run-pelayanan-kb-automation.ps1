param(
    [Parameter(Mandatory = $true)]
    [string]$CommandText
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Node = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"

if (-not (Test-Path $Node)) {
    $Node = "node"
}

$NodeModulesRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules"
$PlaywrightCoreModules = Join-Path $NodeModulesRoot ".pnpm\playwright-core@1.60.0\node_modules"
$PlaywrightModules = Join-Path $NodeModulesRoot ".pnpm\playwright@1.60.0\node_modules"
$env:NODE_PATH = "$PlaywrightCoreModules;$PlaywrightModules"

Push-Location $ProjectRoot
try {
    & $Node ".\scripts\run-pelayanan-kb-automation.cjs" $CommandText
} finally {
    Pop-Location
}
