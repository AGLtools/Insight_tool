@echo off
setlocal enabledelayedexpansion
title Installation - AGL Dashboard
color 09

echo =======================================================
echo     INSTALLATION DU TABLEAU DE BORD AGL
echo =======================================================
echo.
echo Ce script va configurer l'application sur votre PC.
echo Un environnement Python isole sera cree.
echo Ne fermez pas cette fenetre.
echo.

:: Se placer dans le dossier du script
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
%PY% --version
echo.

:: Step 1: Verify pip
echo [1/4] Verification de pip...
%PY% -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [INFO] pip absent, installation via ensurepip...
    %PY% -m ensurepip --upgrade >nul 2>&1
)
echo [OK] pip OK
echo.

:: Step 2: Remove existing venv if present
echo [2/4] Suppression ancienne installation (si presente)...
if exist "%~dp0venv_agl\" (
    rmdir /s /q "%~dp0venv_agl\" >nul 2>&1
    echo [OK] Ancien environnement supprime
) else (
    echo [INFO] Aucune installation anterieure detectee
)
echo.

:: Step 3: Create new venv
echo [3/4] Creation d'un environnement Python isole...
%PY% -m venv "%~dp0venv_agl" --copies
if !errorlevel! neq 0 (
    echo [ERREUR] Echec de la creation du venv
    pause
    exit /b 1
)
echo [OK] Environnement virtuel cree : venv_agl\
echo.

:: Step 4: Install dependencies
echo [4/4] Installation des dependances...
set VENV_PIP="%~dp0venv_agl\Scripts\pip.exe"

%VENV_PIP% install --upgrade pip setuptools wheel --quiet
%VENV_PIP% install -r "%~dp0requirements.txt" --quiet
if !errorlevel! neq 0 (
    echo [ERREUR] Installation des dependances a echoue.
    echo Verifiez votre connexion internet.
    pause
    exit /b 1
)
echo [OK] Toutes les dependances installes avec succes
echo.

echo =======================================================
echo     INSTALLATION REUSSIE !
echo =======================================================
echo.
echo Environnement isole cree dans : venv_agl\
echo Packages installes :
%VENV_PIP% list --quiet
echo.
echo Vous pouvez maintenant lancer l'app avec : Lancer_app.bat
echo.
pause

    %PY% -m ensurepip --default-pip >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible d'installer pip.
        pause
        exit /b 1
    )
)
%PY% -m pip install --upgrade pip -q >nul 2>&1

:: 2. Installer les librairies
echo [2/3] Installation des composants (cela peut prendre quelques minutes)...
%PY% -m pip install -r requirements.txt --no-warn-script-location --break-system-packages
if %errorlevel% neq 0 (
    echo [ERREUR] L'installation des librairies a echoue.
    echo Verifiez votre connexion internet.
    pause
    exit /b 1
)

:: 3. Creer le raccourci sur le bureau
echo [3/3] Creation du raccourci sur le bureau...
call "APPLICATION AGL\Creer_Raccourci_Bureau.bat"

echo.
echo =======================================================
echo     INSTALLATION TERMINEE AVEC SUCCES !
echo =======================================================
echo.
echo  - Une icone "AGL Dashboard" a ete creee sur votre bureau.
echo  - Double-cliquez dessus pour lancer l'application.
echo  - Pour mettre a jour l'app : lancez UPDATE.bat
echo.
echo Vous pouvez maintenant fermer cette fenetre.
echo.
pause
