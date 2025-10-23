
# PowerShell script for installing zit on Windows
$InstallDir = "$env:USERPROFILE\.local\bin"
if (!(Test-Path $InstallDir)) {
	New-Item -ItemType Directory -Path $InstallDir | Out-Null
}
Set-Location $InstallDir
$ReleaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/Thomacdebabo/zit/releases/latest"
$Version = $ReleaseInfo.tag_name
Write-Host "Installing zit version $Version"
# Download the Windows executable (assuming it's named zit.exe)
$DownloadUrl = "https://github.com/Thomacdebabo/zit/releases/download/$Version/zit.exe"
Invoke-WebRequest -Uri $DownloadUrl -OutFile "zit.exe"
Write-Host "zit.exe has been installed to $InstallDir. Add this directory to your PATH if it's not already."