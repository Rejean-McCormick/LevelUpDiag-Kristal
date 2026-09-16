param(
    [string]$Target
)
$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cmd = @((Join-Path $Here "scripts\run_deep_split.py"))
if ($Target) { $Cmd += @("--target", $Target) }
& python @Cmd
exit $LASTEXITCODE
