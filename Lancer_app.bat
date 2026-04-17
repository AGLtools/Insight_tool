@echo off
setlocal enabledelayedexpansion
:: ===========================================
::  LANCEUR AGL DASHBOARD (python_portable)
:: ===========================================
cd /d "%~dp0"

:: Detecte Python : python_portable d'abord, sinon systeme
if exist "%~dp0python_portable\python.exe" (
    set PY="%~dp0python_portable\python.exe"
    echo [INFO] Utilisation de python_portable.
) else (
    python --version >nul 2>&1
    if !errorlevel! equ 0 (
        set PY=python
        echo [INFO] Python systeme detecte.
    ) else (
        echo [ERREUR] Aucun Python trouve !
        echo Placez le dossier python_portable a cote de ce script.
        pause
        exit /b 1
    )
)

:: Lance Streamlit en mode headless et ouvre le navigateur
start "" http://localhost:8501
%PY% -m streamlit run "%~dp0app.py" --server.headless true