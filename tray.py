"""Systeemvak-icoon voor Yellowspot MouseClick."""

import threading

import pystray
from PIL import Image, ImageDraw, ImageFont

APP_NAME = "Yellowspot MouseClick"


def create_icon() -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 59, 59), fill="#FFD200", outline="#111111", width=2)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    draw.text((21, 14), "Y", fill="#111111", font=font)
    return img


class TrayIcon:
    def __init__(self, app):
        self.app = app
        self._icon = pystray.Icon(
            APP_NAME,
            create_icon(),
            APP_NAME,
            menu=pystray.Menu(
                pystray.MenuItem("Openen", self._open),
                pystray.MenuItem("Afsluiten", self._quit),
            ),
        )
        self._icon.default_action = self._open
        threading.Thread(target=self._icon.run, daemon=True).start()

    def _open(self, _icon=None, _item=None):
        self.app.after(0, self.app.show_window)

    def _quit(self, _icon=None, _item=None):
        self.app.after(0, self.app.request_quit)

    def stop(self):
        if self._icon:
            self._icon.stop()
