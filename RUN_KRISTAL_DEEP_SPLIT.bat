@echo off
setlocal
set "HERE=%~dp0"
python "%HERE%scripts\run_deep_split.py" %*
exit /b %ERRORLEVEL%
