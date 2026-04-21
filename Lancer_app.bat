@echo off
setlocal

:: ===========================================
::  LANCEUR AGL DASHBOARD (venv_agl isolated)
:: ===========================================
cd /d "%~dp0"

:: Detect Python: python_portable first, then system
if exist "%~dp0python_portable\python.exe" (
    set "PY=%~dp0python_portable\python.exe"
    goto found_python
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY=python"
    goto found_python
)

echo [ERROR] No Python found.
echo Expected: %~dp0python_portable\python.exe
pause
exit /b 1

:found_python
echo [INFO] Python: %PY%

:: Ensure pip is available on base Python
"%PY%" -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] pip not found, bootstrapping with ensurepip...
    "%PY%" -m ensurepip --upgrade >nul 2>&1
)

:: Create venv on first run
if not exist "%~dp0venv_agl\Scripts\python.exe" (
    echo [INFO] First run - creating isolated environment...
    "%PY%" -m venv "%~dp0venv_agl" --copies
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create venv_agl.
        pause
        exit /b 1
    )
    echo [OK] venv_agl created.
) else (
    echo [INFO] venv_agl already exists.
)

set "VENV_PY=%~dp0venv_agl\Scripts\python.exe"
set "VENV_PIP=%~dp0venv_agl\Scripts\pip.exe"

if not exist "%VENV_PY%" (
    echo [ERROR] Missing venv python: %VENV_PY%
    pause
    exit /b 1
)

if not exist "%VENV_PIP%" (
    echo [ERROR] Missing venv pip: %VENV_PIP%
    pause
    exit /b 1
)

echo [INFO] Installing/updating dependencies...
"%VENV_PIP%" install --upgrade pip setuptools wheel
if %errorlevel% neq 0 (
    echo [ERROR] Failed while upgrading pip/setuptools/wheel.
    pause
    exit /b 1
)

"%VENV_PIP%" install -r "%~dp0requirements.txt"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.txt
    pause
    exit /b 1
)

echo [OK] Dependencies are ready.
echo.
echo ===========================================
echo   STARTING AGL DASHBOARD
echo ===========================================
echo Opening: http://localhost:8501
echo.

start "" http://localhost:8501
"%VENV_PY%" -m streamlit run "%~dp0app.py" --server.headless true

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Streamlit stopped with an error.
    echo Check logs above.
    pause
    exit /b 1
)

pause
