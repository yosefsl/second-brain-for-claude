# Installs the Obsidian second brain for Claude Code on Windows, for the current user. No admin rights.
# Safe to run again. Env (optional): SB_VAULT (default %USERPROFILE%\SecondBrain), SB_RTL (1/0, default 1), SB_NO_OPEN=1
$ErrorActionPreference = "Stop"
$Pkg = Split-Path -Parent $PSScriptRoot
$SbHome = if ($env:SB_HOME) { $env:SB_HOME } else { Join-Path $env:USERPROFILE ".second-brain" }
$Vault = if ($env:SB_VAULT) { $env:SB_VAULT } else { Join-Path $env:USERPROFILE "SecondBrain" }
$Rtl = if ($env:SB_RTL) { $env:SB_RTL } else { "1" }
$env:SB_HOME = $SbHome
New-Item -ItemType Directory -Force -Path $SbHome | Out-Null
function Step($m) { Write-Host "`n==> $m" }

Step "1/4 Python"
$Py = $null
foreach ($c in @("py", "python", "python3")) {
  $cmd = Get-Command $c -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -notlike "*WindowsApps*") {
    try {
      $exe = & $cmd.Source -c "import sys; print(sys.executable if sys.version_info >= (3, 9) else '')" 2>$null
      if ($exe) { $Py = $exe.Trim(); break }
    } catch {}
  }
}
if (-not $Py) {
  $UvDir = Join-Path $SbHome "uv"
  $Uv = Join-Path $UvDir "uv.exe"
  if (-not (Test-Path $Uv)) {
    $env:UV_INSTALL_DIR = $UvDir; $env:UV_NO_MODIFY_PATH = "1"; $env:INSTALLER_NO_MODIFY_PATH = "1"
    powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex" | Out-Null
  }
  $env:UV_PYTHON_INSTALL_DIR = Join-Path $SbHome "python"
  & $Uv python install 3.12 | Out-Null
  $Py = (& $Uv python find 3.12).Trim()
}
Write-Host "python: $Py"

Step "2/4 Obsidian"
$App = Join-Path $env:LOCALAPPDATA "Programs\Obsidian\Obsidian.exe"
if (Test-Path $App) { Write-Host "already installed" }
else {
  $ok = $false
  if (Get-Command winget -ErrorAction SilentlyContinue) {
    winget install --id Obsidian.Obsidian -e --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null
    $ok = Test-Path $App
  }
  if (-not $ok) {
    $rel = Invoke-RestMethod "https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest"
    $asset = $rel.assets | Where-Object { $_.name -match '^Obsidian-[\d\.]+\.exe$' } | Select-Object -First 1
    $exe = Join-Path $env:TEMP $asset.name
    Invoke-WebRequest $asset.browser_download_url -OutFile $exe
    Start-Process $exe -ArgumentList "/S" -Wait
  }
  Write-Host "installed: $App"
}

Step "3/4 Vault and Claude Code"
Get-Process Obsidian -ErrorAction SilentlyContinue | ForEach-Object { $_.CloseMainWindow() | Out-Null }
Start-Sleep -Seconds 2
Get-Process Obsidian -ErrorAction SilentlyContinue | Stop-Process -Force
& $Py (Join-Path $Pkg "tools\setup.py") install --pkg $Pkg --vault $Vault --python $Py --rtl $Rtl
Copy-Item (Join-Path $Pkg "tools\setup.py") (Join-Path $SbHome "setup.py") -Force
& (Join-Path $SbHome "bin\brain.cmd") moc --apply | Out-Null

Step "4/4 Check"
if ($env:SB_NO_OPEN -ne "1" -and (Test-Path $App)) {
  Start-Process ("obsidian://open?path=" + [uri]::EscapeDataString($Vault))
}
& (Join-Path $SbHome "bin\brain.cmd") doctor
if ($LASTEXITCODE -eq 0) { Write-Host "INSTALL_OK vault=$Vault" } else { Write-Host "INSTALL_FAIL see the FAIL lines above"; exit 1 }
