@echo off
setlocal
set "HERE=%~dp0"
pushd "%HERE%"
python -m unittest discover -s tests -v
if errorlevel 1 goto :fail
python levelupdiag.py list
if errorlevel 1 goto :fail
python levelupdiag.py doctor
if errorlevel 1 goto :fail
popd
exit /b 0
:fail
set "ERR=%ERRORLEVEL%"
popd
exit /b %ERR%
