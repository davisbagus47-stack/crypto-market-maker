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
    & $Python run_agent.py --input "data\templates\sample_input_tempat_pelayanan_kb.csv"
} finally {
    Pop-Location
}
