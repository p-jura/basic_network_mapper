@echo off
setlocal
rem Developer/build host only. End users receive Mapper.exe with Python included.
py -3.13 "%~dp0repo\packaging\standalone\prepare_runtime.py" --dest "%~dp0runtime-materials"
if errorlevel 1 exit /b %ERRORLEVEL%
call "%~dp0repo\packaging\standalone\build-windows.cmd" --wheelhouse "%~dp0runtime-wheels" --build-wheels "%~dp0build-wheels" --materials "%~dp0materials" --runtime-materials "%~dp0runtime-materials" --work "%~dp0work" --output "%~dp0dist" --source-revision 20889851ed6a113ba8502f00c279bf954e91b6ba-plus-stage5a
exit /b %ERRORLEVEL%
