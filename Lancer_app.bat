@echo off
:: ===========================================
::  LANCEUR AGL DASHBOARD (python_portable)
:: ===========================================
cd /d "%~dp0"

:: Detecte Python : systeme d'abord, sinon python_portable
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY=python
    echo [INFO] Python systeme detecte.
) else (
    if exist "%~dp0python_portable\python.exe" (
        set PY="%~dp0python_portable\python.exe"
        echo [INFO] Utilisation de python_portable.
    ) else (
        echo [ERREUR] Aucun Python trouve !
        echo Installez Python ou placez le dossier python_portable ici.
        pause
        exit /b 1
    )
)

:: Lance Streamlit en mode headless et ouvre le navigateur
start "" http://localhost:8501
%PY% -m streamlit run "%~dp0app.py" --server.headless true