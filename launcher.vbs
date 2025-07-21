Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = folder
WshShell.Run """" & folder & "\launch_gui.bat""", 0, False
Set WshShell = Nothing
