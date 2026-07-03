#!/usr/bin/env python3
"""Build PPT-Timer into a single-file Windows executable and zip it."""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

APP_NAME = "PPT-Timer"
SCRIPT = "PPT-Timer.py"
ICON = "timer_icon.ico"
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
OUTPUT_ZIP = Path(f"{APP_NAME}.zip")


def run(cmd):
    print("> " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def ensure_pyinstaller():
    if shutil.which("pyinstaller"):
        return
    print("Installing PyInstaller...")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def find_logo():
    for name in os.listdir("."):
        if name.lower().endswith(".png") and "logo" in name.lower():
            return name
    return None


def clean():
    for p in [BUILD_DIR, DIST_DIR, OUTPUT_ZIP]:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()


def main():
    if sys.platform != "win32":
        print("Warning: this app uses Windows APIs; build the exe on Windows.")

    ensure_pyinstaller()
    clean()

    logo = find_logo()
    add_data = []
    if logo:
        add_data.extend(["--add-data", f"{logo};."])

    cmd = [
        "pyinstaller",
        "--onefile",
        "--noconsole",
        "--name", APP_NAME,
        "--icon", ICON,
        "--clean",
        "--noconfirm",
        *add_data,
        SCRIPT,
    ]
    run(cmd)

    # Copy runtime files into dist for the zip
    for f in [ICON]:
        if Path(f).exists():
            shutil.copy(f, DIST_DIR / f)

    # Create zip with only the exe (icon is embedded via --icon)
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        exe = DIST_DIR / f"{APP_NAME}.exe"
        if exe.exists():
            zf.write(exe, arcname=exe.name)

    print(f"\nDone: {OUTPUT_ZIP.resolve()}")
    print(f"Size: {OUTPUT_ZIP.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
