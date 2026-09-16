param(
    [string]$Target
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cmd = @((Join-Path $Here "levelupdiag.py"))
if ($Target) { $Cmd += @("--target", $Target) }
$Cmd += @("run", "deep")
& python @Cmd
exit $LASTEXITCODE
