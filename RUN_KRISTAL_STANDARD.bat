@echo off
setlocal
set "HERE=%~dp0"
python "%HERE%levelupdiag.py" run standard %*
exit /b %ERRORLEVEL%
