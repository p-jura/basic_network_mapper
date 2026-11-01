@echo off
setlocal
rem Build host needs Python 3.13 x64. End-user Mapper.exe does not.
py -3.13 "%~dp0bootstrap.py" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo Budowanie nieudane. Zachowaj kod bledu i katalog roboczy.
exit /b %RESULT%
