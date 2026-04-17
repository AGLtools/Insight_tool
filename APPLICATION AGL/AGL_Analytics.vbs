Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
' Resout le dossier parent a partir de l'emplacement du script lui-meme
sScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
sParent = fso.GetParentFolderName(sScriptDir)
If Right(sParent, 1) <> "\" Then sParent = sParent & "\"
' Lance Lancer_app.bat en mode invisible (0 = fenetre cachee)
WshShell.Run Chr(34) & sParent & "Lancer_app.bat" & Chr(34), 0, False
Set WshShell = Nothing
