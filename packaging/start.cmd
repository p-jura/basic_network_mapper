@echo off
setlocal
if not exist "%~dp0.venv\.mapper-installed.json" (
  echo Najpierw uruchom install.cmd
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" -I "%~dp0bundle.py" start %*
exit /b %errorlevel%
