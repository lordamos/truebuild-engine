Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

strPath = FSO.GetParentFolderName(WScript.ScriptFullName)
strCmd = """" & strPath & "\venv\Scripts\pythonw.exe"" """ & strPath & "\desktop_app.py"""

' If pythonw is not available, fallback to python.exe with hidden window flag (0)
If Not FSO.FileExists(strPath & "\venv\Scripts\pythonw.exe") Then
    strCmd = """" & strPath & "\venv\Scripts\python.exe"" """ & strPath & "\desktop_app.py"""
End If

WshShell.CurrentDirectory = strPath
WshShell.Run strCmd, 0, False
