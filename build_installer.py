"""
OmniTools Studio Pro — Windows Executable Builder (Optimized)
Uses PyInstaller with heavy library exclusions to produce a lean, fast build.
"""

import os
import sys
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def build():
    print("=" * 60)
    print("  Building OmniTools Studio Pro — Windows Standalone App")
    print("=" * 60)

    # Modules to explicitly exclude to prevent bloated build size
    EXCLUDE = [
        "torch", "torchvision", "torchaudio",
        "matplotlib", "sklearn", "scipy", "altair",
        "streamlit", "jupyter", "notebook", "ipython",
        "IPython", "nbconvert", "nbformat", "nbclient",
        "ipykernel", "ipywidgets", "jupyterlab",
        "pandas", "numpy",
        "tensorflow", "keras",
        "pydeck", "plotly", "bokeh",
        "cv2",  # opencv bundled separately
        "xmlrpc", "email", "http.server",
        "unittest", "doctest",
        "test", "tests",
    ]

    exclude_flags = []
    for mod in EXCLUDE:
        exclude_flags.extend(["--exclude-module", mod])

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=OmniTools_Studio_Pro",
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--clean",
        # Explicit data collection for runtime assets
        "--collect-data=customtkinter",
        "--collect-data=textual",
        # Add local modules directory
        f"--add-data={os.path.join(ROOT_DIR, 'modules')}{os.pathsep}modules",
        # Optimizations
        "--noupx",              # Skip UPX compression (avoids AV false positives)
        # NOTE: --strip is Linux/Mac only, omit on Windows
    ] + exclude_flags + [
        os.path.join(ROOT_DIR, "main.py")
    ]

    print("\nRunning PyInstaller... This may take 2-5 minutes.\n")
    res = subprocess.run(cmd, cwd=ROOT_DIR)

    if res.returncode == 0:
        exe_path = os.path.join(ROOT_DIR, "dist", "OmniTools_Studio_Pro", "OmniTools_Studio_Pro.exe")
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n[SUCCESS] Built: {exe_path}  ({size_mb:.1f} MB)")
        create_installer()
    else:
        print("\n[FAILED] Build failed — check output above for errors.")


def create_installer():
    dist_dir = os.path.join(ROOT_DIR, "dist")

    # PowerShell shortcut script
    ps_code = r"""
param()
$WshShell = New-Object -ComObject WScript.Shell
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetExe = Join-Path $ScriptDir "OmniTools_Studio_Pro\OmniTools_Studio_Pro.exe"
$Desktop = [Environment]::GetFolderPath("Desktop")

if (Test-Path $TargetExe) {
    # GUI Shortcut
    $s1 = $WshShell.CreateShortcut("$Desktop\OmniTools Studio Pro.lnk")
    $s1.TargetPath = $TargetExe
    $s1.Arguments = "--gui"
    $s1.WorkingDirectory = (Split-Path $TargetExe)
    $s1.Description = "OmniTools Studio Pro — High-Spec Desktop App"
    $s1.Save()
    Write-Host "[OK] Desktop shortcut: OmniTools Studio Pro.lnk" -ForegroundColor Green
} else {
    Write-Host "[ERROR] EXE not found: $TargetExe" -ForegroundColor Red
}
"""

    bat_code = """@echo off
title OmniTools Studio Pro — Windows Installer
echo =====================================================
echo    OmniTools Studio Pro — Windows Setup Installer
echo =====================================================
echo.
echo Creating Desktop shortcut...
powershell -ExecutionPolicy Bypass -File "%~dp0install_shortcuts.ps1"
echo.
echo Done! OmniTools Studio Pro shortcut added to your Desktop.
echo.
set /p launch="Launch OmniTools Studio Pro now? (Y/N): "
if /i "%launch%"=="Y" (
    start "" "%~dp0OmniTools_Studio_Pro\\OmniTools_Studio_Pro.exe"
)
"""

    with open(os.path.join(dist_dir, "install_shortcuts.ps1"), "w", encoding="utf-8") as f:
        f.write(ps_code)

    with open(os.path.join(dist_dir, "Install_OmniTools_Setup.bat"), "w", encoding="utf-8") as f:
        f.write(bat_code)

    print(f"\n[SUCCESS] Installer package created in: {dist_dir}")
    print(f"  >> Run  dist/Install_OmniTools_Setup.bat  to install to your Windows Desktop.")


if __name__ == "__main__":
    build()
