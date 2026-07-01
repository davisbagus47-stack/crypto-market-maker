param(
    [Parameter(Mandatory = $true)]
    [string]$CommandText
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if (Test-Path $BundledPython) {
    $Python = $BundledPython
} else {
    $Python = "python"
}

Push-Location $ProjectRoot
try {
    & $Python parse_command.py $CommandText
} finally {
    Pop-Location
}
