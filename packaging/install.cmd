@echo off
setlocal
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3.13 -I "%~dp0bundle.py" install
exit /b %errorlevel%
:usepython
python -I "%~dp0bundle.py" install
exit /b %errorlevel%
