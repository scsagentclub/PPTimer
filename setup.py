import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["tkinter", "PIL"],
    "includes": ["os", "sys", "json", "ctypes"],
    "include_files": ["timer_icon.ico"],
    "excludes": ["unittest", "email", "http", "xml", "pydoc"],
}

bdist_msi_options = {
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\PPTimer",
}

base = "Win32GUI" if sys.platform == "win32" else None

executables = [
    Executable(
        "PPT-Timer.py",
        base=base,
        target_name="PPTimer.exe",
        icon="timer_icon.ico",
        shortcut_name="PPTimer",
        shortcut_dir="ProgramMenuFolder",
    )
]

setup(
    name="PPTimer",
    version="1.1.0",
    description="A lifetime-free PowerPoint countdown timer.",
    author="scsagentclub",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
