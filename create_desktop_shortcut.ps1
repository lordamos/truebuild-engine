$desktopPath = [Environment]::GetFolderPath("Desktop")
$targetVbs = "C:\Users\Darwin\pubkisher\truebuild\Launch-TrueBuild-Desktop.vbs"
$workingDir = "C:\Users\Darwin\pubkisher\truebuild"
$shortcutFile = Join-Path $desktopPath "TrueBuild Suite.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutFile)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$targetVbs`""
$Shortcut.WorkingDirectory = $workingDir
$Shortcut.Description = "TrueBuild Dual-Threat Desktop Suite (Corporate Credit & Personal Credit CRM)"
$Shortcut.IconLocation = "shell32.dll, 45" # Shield / Vault icon from Windows system icons
$Shortcut.Save()

Write-Output "Successfully created shortcut at: $shortcutFile"
