@echo off
:: ===========================================
::  Cree un raccourci "AGL Dashboard"
::  - Dans le Menu Demarrer (pour epingler a la barre des taches)
::  - Sur le bureau local %USERPROFILE%\Desktop
:: ===========================================
cd /d "%~dp0"

set STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs
set LOCALDESKTOP=%USERPROFILE%\Documents

:: --- Raccourci Menu Demarrer ---
set SCRIPT="%TEMP%\agl_shortcut_%RANDOM%.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT%
echo Set oLink = oWS.CreateShortcut("%STARTMENU%\AGL Dashboard.lnk") >> %SCRIPT%
echo oLink.TargetPath = "%~dp0AGL_Analytics.vbs" >> %SCRIPT%
echo oLink.WorkingDirectory = "%~dp0.." >> %SCRIPT%
echo oLink.Description = "Tableau de Bord Part de Marche AGL" >> %SCRIPT%
echo oLink.IconLocation = "%~dp0..\Images\Logo_AGL.ico" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

:: --- Raccourci Bureau local ---
set SCRIPT2="%TEMP%\agl_shortcut2_%RANDOM%.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") > %SCRIPT2%
echo Set oLink = oWS.CreateShortcut("%LOCALDESKTOP%\AGL Dashboard.lnk") >> %SCRIPT2%
echo oLink.TargetPath = "%~dp0AGL_Analytics.vbs" >> %SCRIPT2%
echo oLink.WorkingDirectory = "%~dp0.." >> %SCRIPT2%
echo oLink.Description = "Tableau de Bord Part de Marche AGL" >> %SCRIPT2%
echo oLink.IconLocation = "%~dp0..\Images\Logo_AGL.ico" >> %SCRIPT2%
echo oLink.Save >> %SCRIPT2%

cscript /nologo %SCRIPT2%
del %SCRIPT2%
