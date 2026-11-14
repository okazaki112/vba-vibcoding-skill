@echo off
setlocal
rem Validate entry: detect Python then run structural + acceptance checks.
set "PYEX="
where py >nul 2>nul && set "PYEX=py -3"
if not defined PYEX where python >nul 2>nul && set "PYEX=python"
if not defined PYEX where python3 >nul 2>nul && set "PYEX=python3"
if not defined PYEX (
  echo [ERR] No Python runtime detected. Domain scripts do not require Python;
  echo [ERR] only the meta validators validate.py / validate_acceptance.py do.
  echo [ERR] Install Python 3 or run the two checks on a machine that has it.
  exit /b 2
)
%PYEX% -X utf8 "%~dp0scripts\validate.py" "%~dp0."
if errorlevel 1 exit /b 1
%PYEX% -X utf8 "%~dp0scripts\validate_acceptance.py" "%~dp0."
if errorlevel 1 exit /b 1
echo [OK] All validations passed.
endlocal
