"""Windows 'Start met Windows' via de HKCU Run-sleutel."""

import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Yellowspot MouseClick"


def launch_command(minimized: bool = False) -> str:
    extra = " --startup"
    if minimized:
        extra += " --minimized"
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"{extra}'
    script = Path(__file__).resolve().parent / "main.py"
    return f'"{sys.executable}" "{script}"{extra}'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, VALUE_NAME)
            return bool(value)
    except OSError:
        return False


def set_enabled(enabled: bool, minimized: bool = False) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, launch_command(minimized))
            return
        try:
            winreg.DeleteValue(key, VALUE_NAME)
        except FileNotFoundError:
            pass
