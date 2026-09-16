$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $Here
try {
  python -m unittest discover -s tests -v
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  python levelupdiag.py list
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  python levelupdiag.py doctor
  exit $LASTEXITCODE
}
finally {
  Pop-Location
}
