@echo off
title Mise a jour - AGL Dashboard
color 0A

echo =======================================================
echo     MISE A JOUR DU TABLEAU DE BORD AGL
echo =======================================================
echo.
echo Telechargement de la derniere version depuis GitHub...
echo.

cd /d "%~dp0"

:: Detecte Python : systeme d'abord, sinon python_portable
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY=python
) else (
    if exist "%~dp0python_portable\python.exe" (
        set PY="%~dp0python_portable\python.exe"
    ) else (
        echo [ERREUR] Aucun Python trouve !
        pause
        exit /b 1
    )
)

set REPO_URL=https://raw.githubusercontent.com/AGLtools/Insight_tool/master

:: ---- 1. Application principale ----
echo [1/6] Telechargement de app.py...
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/app.py', 'app.py')"
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible de telecharger app.py
    echo Verifiez votre connexion internet.
    pause
    exit /b 1
)

:: ---- 2. Dependances ----
echo [2/6] Telechargement de requirements.txt...
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/requirements.txt', 'requirements.txt')"

:: ---- 3. Scripts de lancement et installation ----
echo [3/6] Mise a jour des scripts...
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/INSTALLATION.bat', 'INSTALLATION.bat')"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/Lancer_app.bat', 'Lancer_app.bat')"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/UPDATE.bat', 'UPDATE.bat')"

:: ---- 4. Scripts APPLICATION AGL ----
echo [4/6] Mise a jour des fichiers application...
if not exist "APPLICATION AGL" mkdir "APPLICATION AGL"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/APPLICATION%%20AGL/AGL_Analytics.vbs', 'APPLICATION AGL\\AGL_Analytics.vbs')"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/APPLICATION%%20AGL/Creer_Raccourci_Bureau.bat', 'APPLICATION AGL\\Creer_Raccourci_Bureau.bat')"

:: ---- 5. Installation des librairies ----
echo [5/6] Installation des dependances...
%PY% -m pip install -r requirements.txt -q --no-warn-script-location 2>nul

:: ---- 6. Recreer le raccourci bureau (au cas ou le chemin a change) ----
echo [6/6] Mise a jour du raccourci bureau...
call "APPLICATION AGL\Creer_Raccourci_Bureau.bat"

echo.
echo =======================================================
echo     MISE A JOUR TERMINEE !
echo =======================================================
echo.
echo L'application a ete mise a jour avec succes.
echo Relancez le raccourci "AGL Dashboard" sur votre bureau.
echo.
pause
