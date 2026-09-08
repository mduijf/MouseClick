"""Windows toetsaanslag-simulatie via user32.dll."""

import ctypes
import sys

if sys.platform != "win32":
    raise OSError("Deze applicatie werkt alleen op Windows.")

user32 = ctypes.windll.user32

KEYEVENTF_KEYUP = 0x0002

# Windows virtual key codes
VK = {
    "BACKSPACE": 0x08,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "ESCAPE": 0x1B,
    "ESC": 0x1B,
    "SPACE": 0x20,
    "PAGEUP": 0x21,
    "PAGEDOWN": 0x22,
    "END": 0x23,
    "HOME": 0x24,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "INSERT": 0x2D,
    "DELETE": 0x2E,
    "0": 0x30,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
    "6": 0x36,
    "7": 0x37,
    "8": 0x38,
    "9": 0x39,
    "A": 0x41,
    "B": 0x42,
    "C": 0x43,
    "D": 0x44,
    "E": 0x45,
    "F": 0x46,
    "G": 0x47,
    "H": 0x48,
    "I": 0x49,
    "J": 0x4A,
    "K": 0x4B,
    "L": 0x4C,
    "M": 0x4D,
    "N": 0x4E,
    "O": 0x4F,
    "P": 0x50,
    "Q": 0x51,
    "R": 0x52,
    "S": 0x53,
    "T": 0x54,
    "U": 0x55,
    "V": 0x56,
    "W": 0x57,
    "X": 0x58,
    "Y": 0x59,
    "Z": 0x5A,
    "F1": 0x70,
    "F2": 0x71,
    "F3": 0x72,
    "F4": 0x73,
    "F5": 0x74,
    "F6": 0x75,
    "F7": 0x76,
    "F8": 0x77,
    "F9": 0x78,
    "F10": 0x79,
    "F11": 0x7A,
    "F12": 0x7B,
}

# Tk keysym → canonical display name
KEYSYM_TO_NAME = {
    "Return": "Enter",
    "Escape": "Escape",
    "BackSpace": "Backspace",
    "Delete": "Delete",
    "Tab": "Tab",
    "space": "Space",
    "Prior": "PageUp",
    "Next": "PageDown",
    "Home": "Home",
    "End": "End",
    "Left": "Left",
    "Up": "Up",
    "Right": "Right",
    "Down": "Down",
    "Insert": "Insert",
}


def keysym_to_name(keysym: str) -> str:
    if keysym in KEYSYM_TO_NAME:
        return KEYSYM_TO_NAME[keysym]
    if keysym.startswith("F") and keysym[1:].isdigit():
        return keysym.upper()
    if len(keysym) == 1:
        return keysym.upper()
    return keysym


def parse_key(name: str) -> int:
    key = name.strip()
    if not key:
        raise ValueError("Geen toets opgegeven")
    normalized = key.upper()
    if normalized in VK:
        return VK[normalized]
    if len(key) == 1:
        char = key.upper()
        if char in VK:
            return VK[char]
    raise ValueError(f"Onbekende toets: {name}")


def press_key(key: str) -> None:
    vk = parse_key(key)
    user32.keybd_event(vk, 0, 0, 0, 0)
    user32.keybd_event(vk, 0, 0, KEYEVENTF_KEYUP, 0)
