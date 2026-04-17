Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
' Resout le dossier parent a partir de l'emplacement du script lui-meme
sScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
sParent = fso.GetParentFolderName(sScriptDir)
If Right(sParent, 1) <> "\" Then sParent = sParent & "\"

sBat = sParent & "Lancer_app.bat"
sPy = sParent & "python_portable\python.exe"

' Verifie que les fichiers existent avant de lancer
If Not fso.FileExists(sBat) Then
    MsgBox "Fichier introuvable :" & vbCrLf & sBat, vbCritical, "AGL Dashboard - Erreur"
    WScript.Quit 1
End If

If Not fso.FolderExists(sParent & "python_portable") Then
    MsgBox "Le dossier python_portable est introuvable :" & vbCrLf & sParent & "python_portable", vbCritical, "AGL Dashboard - Erreur"
    WScript.Quit 1
End If

' Lance Lancer_app.bat en mode minimise (7) pour voir les erreurs si besoin
WshShell.Run Chr(34) & sBat & Chr(34), 7, False
Set WshShell = Nothing
