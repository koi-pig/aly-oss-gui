$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

python -m pip install -r requirements.txt

if (Test-Path .\dist) {
    Get-ChildItem .\dist -Filter "*.exe" | Remove-Item -Force
}

python -m PyInstaller --clean --noconfirm --onefile --windowed --icon .\assets\app.ico --add-data ".\assets\app.ico;assets" --name AlyOssTool gui.py
Copy-Item -Path .\config.local.json -Destination .\dist\config.local.json -Force
Write-Host "????: $ProjectDir\dist\AlyOssTool.exe"
