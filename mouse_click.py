"""Windows muisklik-simulatie via user32.dll."""

import ctypes
import sys
import time

if sys.platform != "win32":
    raise OSError("Deze applicatie werkt alleen op Windows.")

user32 = ctypes.windll.user32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010


def get_cursor_pos() -> tuple[int, int]:
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    point = POINT()
    user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


def _press(button: str, down: bool) -> None:
    if button == "right":
        flag = MOUSEEVENTF_RIGHTDOWN if down else MOUSEEVENTF_RIGHTUP
    else:
        flag = MOUSEEVENTF_LEFTDOWN if down else MOUSEEVENTF_LEFTUP
    user32.mouse_event(flag, 0, 0, 0, 0)


def click(x: int, y: int, button: str = "left", double: bool = False) -> None:
    user32.SetCursorPos(int(x), int(y))
    _press(button, True)
    _press(button, False)
    if double:
        time.sleep(0.05)
        _press(button, True)
        _press(button, False)
