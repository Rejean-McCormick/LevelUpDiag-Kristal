$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
& python (Join-Path $Here "scripts\run_deep_split.py") @args
exit $LASTEXITCODE
