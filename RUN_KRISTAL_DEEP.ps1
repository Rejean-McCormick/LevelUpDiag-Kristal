$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
& python (Join-Path $Here "levelupdiag.py") run deep @args
exit $LASTEXITCODE
