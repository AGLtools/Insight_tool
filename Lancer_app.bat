@echo off
setlocal enabledelayedexpansion
:: ===========================================
::  LANCEUR AGL DASHBOARD (python_portable)
:: ===========================================
cd /d "%~dp0"

:: Detecte Python : python_portable d'abord, sinon systeme
if exist "%~dp0python_portable\python.exe" (
    set PY="%~dp0python_portable\python.exe"
    goto :found_python
)

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PY=python
    goto :found_python
)

echo [ERREUR] Aucun Python trouve !
echo Placez le dossier python_portable a cote de ce script.
echo Chemin attendu : %~dp0python_portable\python.exe
pause
exit /b 1

:found_python
echo [INFO] Python : %PY%

:: Supprimer le verrou EXTERNALLY-MANAGED si present (python_portable)
if exist "%~dp0python_portable\Lib\EXTERNALLY-MANAGED" del /f "%~dp0python_portable\Lib\EXTERNALLY-MANAGED"
dir /b /ad "%~dp0python_portable\Lib\python*" >nul 2>&1 && (
    for /f "delims=" %%D in ('dir /b /ad "%~dp0python_portable\Lib\python*" 2^>nul') do (
        if exist "%~dp0python_portable\Lib\%%D\EXTERNALLY-MANAGED" del /f "%~dp0python_portable\Lib\%%D\EXTERNALLY-MANAGED"
    )
)

:: S'assurer que pip est disponible
%PY% -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] pip absent, bootstrap via ensurepip...
    %PY% -m ensurepip --upgrade >nul 2>&1
)
%PY% -m pip install --upgrade pip setuptools wheel --no-warn-script-location --break-system-packages -q >nul 2>&1

:: Verification et installation des packages requis
echo [INFO] Verification des dependances...
%PY% -m pip install -r "%~dp0requirements.txt" --no-warn-script-location --break-system-packages
if !errorlevel! neq 0 (
    echo [ERREUR] L'installation des dependances a echoue.
    echo Verifiez votre connexion internet.
    pause
    exit /b 1
)
echo [INFO] Toutes les dependances sont OK.


:: Lance Streamlit en mode headless et ouvre le navigateur
start "" http://localhost:8501
%PY% -m streamlit run "%~dp0app.py" --server.headless true

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Streamlit s'est arrete avec une erreur.
    pause
)