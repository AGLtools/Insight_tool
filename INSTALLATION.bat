@echo off
setlocal enabledelayedexpansion
title Installation - AGL Dashboard
color 09

echo =======================================================
echo     INSTALLATION DU TABLEAU DE BORD AGL
echo =======================================================
echo.
echo Ce script va configurer l'application sur votre PC.
echo Aucun Python n'est requis - tout est inclus.
echo Ne fermez pas cette fenetre.
echo.

:: Se placer dans le dossier du script
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

:: 1. Verifier pip
echo [1/3] Verification de pip...
%PY% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] pip absent, installation via ensurepip...
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
%PY% -m pip install -r requirements.txt --no-warn-script-location
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
