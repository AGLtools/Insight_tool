@echo off
setlocal enabledelayedexpansion
title Mise a jour - AGL Dashboard
color 0A

echo =======================================================
echo     MISE A JOUR DU TABLEAU DE BORD AGL
echo =======================================================
echo.

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
pause
exit /b 1

:found_python
echo [INFO] Python : %PY%

set REPO_OWNER=AGLtools
set REPO_NAME=Insight_tool
set BRANCH=Deployment
set REPO_URL=https://raw.githubusercontent.com/%REPO_OWNER%/%REPO_NAME%/%BRANCH%
set API_URL=https://api.github.com/repos/%REPO_OWNER%/%REPO_NAME%/commits/%BRANCH%

:: ---- Verification de mise a jour ----
echo [*] Verification de mise a jour...
echo.

set COMMIT_SHA=inconnu
set COMMIT_MSG=
set COMMIT_AUTHOR=
set COMMIT_DATE=
set SKIP_CHECK=0

%PY% -c "import urllib.request, json; data=json.loads(urllib.request.urlopen('%API_URL%').read()); print('COMMIT_SHA=' + data['sha'][:7]); print('COMMIT_MSG=' + data['commit']['message'].split(chr(10))[0]); print('COMMIT_AUTHOR=' + data['commit']['author']['name']); print('COMMIT_DATE=' + data['commit']['author']['date'][:10])" > "%TEMP%\agl_commit_info.txt" 2>nul

if %errorlevel% neq 0 (
    echo [INFO] Impossible de verifier la version via l'API GitHub.
    echo [INFO] L'API est peut-etre bloquee par le reseau. Mise a jour forcee...
    echo.
    set SKIP_CHECK=1
    goto :start_download
)

:: Lire les infos du commit
for /f "tokens=1,* delims==" %%A in (%TEMP%\agl_commit_info.txt) do set %%A=%%B
del "%TEMP%\agl_commit_info.txt" >nul 2>&1

:: Comparer avec la version locale
set VERSION_FILE=%~dp0.current_version
set LOCAL_SHA=
if exist "%VERSION_FILE%" (
    set /p LOCAL_SHA=<"%VERSION_FILE%"
)

if "!LOCAL_SHA!"=="!COMMIT_SHA!" (
    echo.
    echo    Aucune mise a jour disponible.
    echo    Vous etes deja sur la derniere version [%COMMIT_SHA%].
    echo    Message : %COMMIT_MSG%
    echo.
    pause
    exit /b 0
)

echo    Mise a jour trouvee !
echo    -----------------------------------------------
echo    Commit  : %COMMIT_SHA%
echo    Message : %COMMIT_MSG%
echo    Auteur  : %COMMIT_AUTHOR%
echo    Date    : %COMMIT_DATE%
echo    -----------------------------------------------
echo.

:start_download

:: ---- 1. Application principale ----
echo [1/8] Telechargement de app.py...
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/app.py', 'app.py')"
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible de telecharger app.py
    echo Verifiez votre connexion internet.
    pause
    exit /b 1
)

:: ---- 2. Dependances ----
echo [2/8] Telechargement de requirements.txt...
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/requirements.txt', 'requirements.txt')"

:: ---- 3. Scripts de lancement et installation ----
echo [3/8] Mise a jour des scripts...
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/INSTALLATION.bat', 'INSTALLATION.bat')"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/Lancer_app.bat', 'Lancer_app.bat')"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/UPDATE.bat', 'UPDATE.bat')"

:: ---- 4. Scripts APPLICATION AGL ----
echo [4/8] Mise a jour des fichiers application...
if not exist "APPLICATION AGL" mkdir "APPLICATION AGL"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/APPLICATION%%20AGL/AGL_Analytics.vbs', 'APPLICATION AGL\\AGL_Analytics.vbs')"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/APPLICATION%%20AGL/Creer_Raccourci_Bureau.bat', 'APPLICATION AGL\\Creer_Raccourci_Bureau.bat')"

:: ---- 5. Configuration Streamlit ----
echo [5/8] Mise a jour de la configuration Streamlit...
if not exist ".streamlit" mkdir ".streamlit"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/.streamlit/config.toml', '.streamlit\\config.toml')"

:: ---- 6. Images ----
echo [6/8] Mise a jour des images...
if not exist "Images" mkdir "Images"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/Images/Logo%%20_AGL.png', 'Images\\Logo _AGL.png')"
%PY% -c "import urllib.request; urllib.request.urlretrieve('%REPO_URL%/Images/Logo_AGL.ico', 'Images\\Logo_AGL.ico')"

:: ---- 7. Installation des librairies ----
echo [7/8] Installation des dependances...
%PY% -m pip install -r requirements.txt -q --no-warn-script-location 2>nul

:: ---- 8. Recreer le raccourci ----
echo [8/8] Mise a jour du raccourci...
call "APPLICATION AGL\Creer_Raccourci_Bureau.bat"

:: Sauvegarder la version installee
if not "!COMMIT_SHA!"=="inconnu" (
    echo !COMMIT_SHA!> "%~dp0.current_version"
)

echo.
echo =======================================================
echo     MISE A JOUR TERMINEE !  [!COMMIT_SHA!]
echo =======================================================
echo.
echo  Version : %COMMIT_MSG%
echo  Date    : %COMMIT_DATE%
echo.
echo L'application a ete mise a jour avec succes.
echo Relancez le raccourci "AGL Dashboard".
echo.
pause
