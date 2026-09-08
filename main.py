"""
Yellowspot MouseClick — simuleer muisklikken en toetsaanslagen op instelbare tijden (Windows).
"""

import json
import sys
import threading
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

if sys.platform != "win32":
    _err = tk.Tk()
    _err.withdraw()
    messagebox.showerror("Yellowspot MouseClick", "Deze app werkt alleen op Windows.")
    sys.exit(1)

from autostart import set_enabled as set_windows_autostart
from key_press import keysym_to_name, parse_key, press_key
from mouse_click import click, get_cursor_pos
from tray import APP_NAME, TrayIcon
from version import version_label


def config_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "clicks.json"
    return Path(__file__).parent / "clicks.json"


class Scheduler:
    def __init__(self, set_status, on_done):
        self._stop = threading.Event()
        self._thread = None
        self.set_status = set_status
        self.on_done = on_done

    @property
    def running(self):
        return self._thread and self._thread.is_alive()

    def start(self, clicks, repeat, pause):
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, args=(clicks, repeat, pause), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self, clicks, repeat, pause):
        try:
            while not self._stop.is_set():
                for i, c in enumerate(clicks):
                    if self._stop.is_set():
                        break
                    self._wait(c)
                    if self._stop.is_set():
                        break
                    if c.get("type", "click") == "key":
                        self.set_status(f"Toets {c['key']} {i + 1}/{len(clicks)}")
                        press_key(c["key"])
                    else:
                        kind = "dubbelklik" if c.get("double") else "klik"
                        self.set_status(f"{kind.capitalize()} {i + 1}/{len(clicks)} op ({c['x']}, {c['y']})")
                        click(c["x"], c["y"], double=c.get("double", False))
                if not repeat or self._stop.is_set():
                    break
                self.set_status(f"Pauze {pause}s...")
                if self._stop.wait(pause):
                    break
            self.set_status("Klaar" if not self._stop.is_set() else "Gestopt")
        except Exception as e:
            self.set_status(f"Fout: {e}")
        finally:
            self.on_done()

    def _wait(self, click_def):
        mode = click_def.get("mode", "delay")
        if mode == "delay":
            sec = float(click_def["delay"])
            if sec <= 0:
                return
            self.set_status(f"Wachten {sec:g}s...")
            self._stop.wait(sec)
            return

        h, m, s = map(int, click_def["time"].split(":"))
        target = datetime.now().replace(hour=h, minute=m, second=s, microsecond=0)
        if target <= datetime.now():
            target += timedelta(days=1)
        self.set_status(f"Wachten tot {target:%H:%M:%S}...")
        while not self._stop.is_set():
            left = (target - datetime.now()).total_seconds()
            if left <= 0:
                break
            self._stop.wait(min(left, 0.25))


class App(tk.Tk):
    BG = "#f5f5f5"
    ACCENT = "#2563eb"

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {version_label()}")
        self.geometry("440x760")
        self.minsize(400, 640)
        self.configure(bg=self.BG)

        self.clicks: list[dict] = []
        self._in_tray = False
        self._capturing_key = False
        self._tray: TrayIcon | None = None
        self._from_windows = "--startup" in sys.argv or "--minimized" in sys.argv
        self._launch_minimized = "--minimized" in sys.argv
        self.scheduler = Scheduler(self._status, self._done)
        self._build()
        self._load()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Unmap>", self._on_unmap)
        self.bind("<Configure>", self._on_resize)
        self._tray = TrayIcon(self)
        self.after(200, self._apply_launch_behavior)

    def _build(self):
        # Onderkant eerst — blijft altijd zichtbaar bij verkleinen
        footer = tk.Frame(self, bg=self.BG)
        footer.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=(8, 12))

        self.status = tk.StringVar(value="Gereed — voeg acties toe en druk op Start")
        self.status_label = tk.Label(
            footer, textvariable=self.status, bg=self.BG, fg="#555",
            font=("Segoe UI", 9), wraplength=400, justify=tk.LEFT, anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X, pady=(0, 8))

        ctrl = tk.Frame(footer, bg=self.BG)
        ctrl.pack(fill=tk.X, pady=(0, 8))
        self.btn_start = tk.Button(
            ctrl, text="▶  START", font=("Segoe UI", 11, "bold"),
            bg=self.ACCENT, fg="white", relief=tk.FLAT, padx=20, pady=8,
            cursor="hand2", command=self._start,
        )
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_stop = tk.Button(
            ctrl, text="■  STOP", font=("Segoe UI", 11, "bold"),
            bg="#dc2626", fg="white", relief=tk.FLAT, padx=20, pady=8,
            cursor="hand2", command=self._stop, state=tk.DISABLED,
        )
        self.btn_stop.pack(side=tk.LEFT)

        opts = tk.Frame(footer, bg=self.BG)
        opts.pack(fill=tk.X)
        self.repeat = tk.BooleanVar()
        ttk.Checkbutton(
            opts, text="Herhalen", variable=self.repeat, command=self._save,
        ).pack(side=tk.LEFT)
        tk.Label(opts, text="Pauze (sec)", bg=self.BG).pack(side=tk.LEFT, padx=(12, 4))
        self.pause = tk.StringVar(value="5")
        ttk.Entry(opts, textvariable=self.pause, width=5).pack(side=tk.LEFT)

        boot = tk.Frame(footer, bg=self.BG)
        boot.pack(fill=tk.X, pady=(10, 0))
        tk.Label(boot, text="Opstarten", bg=self.BG, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.start_with_windows = tk.BooleanVar()
        self.autorun = tk.BooleanVar()
        self.start_in_tray = tk.BooleanVar()
        ttk.Checkbutton(
            boot, text="Start met Windows",
            variable=self.start_with_windows, command=self._on_start_with_windows,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            boot, text="Acties automatisch uitvoeren bij opstarten",
            variable=self.autorun, command=self._save,
        ).pack(anchor=tk.W)
        ttk.Checkbutton(
            boot, text="Start in systeemvak",
            variable=self.start_in_tray, command=self._on_start_in_tray,
        ).pack(anchor=tk.W)
        tk.Label(
            boot,
            text="Voor een klik 1 minuut na opstarten: eerste actie op 60 seconden vertraging.",
            bg=self.BG, fg="#666", font=("Segoe UI", 8), wraplength=400, justify=tk.LEFT, anchor=tk.W,
        ).pack(fill=tk.X, pady=(2, 0))

        content = tk.Frame(self, bg=self.BG)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        header = tk.Label(
            content, text=f"{APP_NAME} {version_label()}", font=("Segoe UI", 16, "bold"),
            bg=self.BG, fg="#111",
        )
        header.pack(pady=(16, 2))
        tk.Label(
            content, text="Plan muisklikken en toetsaanslagen op tijd",
            font=("Segoe UI", 10), bg=self.BG, fg="#555",
        ).pack(pady=(0, 4))
        tk.Label(
            content, text="Minimaliseer om op de achtergrond te draaien (systeemvak)",
            font=("Segoe UI", 9), bg=self.BG, fg="#888",
        ).pack(pady=(0, 10))

        form = tk.Frame(content, bg="white", highlightbackground="#ddd", highlightthickness=1)
        form.pack(fill=tk.X, padx=16, pady=4)

        inner = tk.Frame(form, bg="white", padx=12, pady=12)
        inner.pack(fill=tk.X)

        self.action_type = tk.StringVar(value="click")
        action_row = tk.Frame(inner, bg="white")
        action_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(action_row, text="Actie", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        ttk.Radiobutton(
            action_row, text="Muisklik",
            variable=self.action_type, value="click", command=self._update_action_fields,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            action_row, text="Toetsaanslag",
            variable=self.action_type, value="key", command=self._update_action_fields,
        ).pack(anchor=tk.W)

        self.mode = tk.StringVar(value="delay")
        mode_row = tk.Frame(inner, bg="white")
        mode_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(mode_row, text="Timing", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        ttk.Radiobutton(
            mode_row, text="Vertraging — wacht X seconden na vorige actie",
            variable=self.mode, value="delay", command=self._update_value_field,
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            mode_row, text="Kloktijd — actie op een vast tijdstip vandaag",
            variable=self.mode, value="clock", command=self._update_value_field,
        ).pack(anchor=tk.W)

        self.val = tk.StringVar(value="3")
        row1 = tk.Frame(inner, bg="white")
        row1.pack(fill=tk.X, pady=4)
        self.val_label = tk.Label(row1, text="Seconden", bg="white", width=12, anchor=tk.W)
        self.val_label.pack(side=tk.LEFT)
        self.val_entry = ttk.Entry(row1, textvariable=self.val, width=28)
        self.val_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.val_hint = tk.Label(
            inner, text="Aantal seconden wachten vóór deze actie.",
            bg="white", fg="#666", font=("Segoe UI", 8), anchor=tk.W,
        )
        self.val_hint.pack(fill=tk.X, pady=(0, 4))

        self.click_fields = tk.Frame(inner, bg="white")
        self.click_fields.pack(fill=tk.X)

        self.x = tk.StringVar(value="500")
        self.y = tk.StringVar(value="400")
        row2 = tk.Frame(self.click_fields, bg="white")
        row2.pack(fill=tk.X, pady=4)
        tk.Label(row2, text="X", bg="white", width=8, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.x, width=10).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(row2, text="Y", bg="white").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Entry(row2, textvariable=self.y, width=10).pack(side=tk.LEFT)

        self.double = tk.BooleanVar(value=False)
        row3 = tk.Frame(self.click_fields, bg="white")
        row3.pack(fill=tk.X, pady=4)
        ttk.Checkbutton(row3, text="Dubbelklik", variable=self.double).pack(anchor=tk.W)
        ttk.Button(self.click_fields, text="Huidige positie", command=self._pick_pos).pack(anchor=tk.W, pady=(4, 0))

        self.key_fields = tk.Frame(inner, bg="white")
        self.key = tk.StringVar(value="F6")
        key_row = tk.Frame(self.key_fields, bg="white")
        key_row.pack(fill=tk.X, pady=4)
        tk.Label(key_row, text="Toets", bg="white", width=8, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Entry(key_row, textvariable=self.key, width=12).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(key_row, text="Toets kiezen", command=self._capture_key).pack(side=tk.LEFT)
        tk.Label(
            self.key_fields,
            text="Bijv. F6, Enter, Tab, A. Of klik op Toets kiezen en druk een toets.",
            bg="white", fg="#666", font=("Segoe UI", 8), anchor=tk.W,
        ).pack(fill=tk.X, pady=(0, 4))

        self.form_btns = tk.Frame(inner, bg="white")
        self.form_btns.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(self.form_btns, text="+ Toevoegen", command=self._add).pack(side=tk.LEFT)

        list_frame = tk.Frame(content, bg=self.BG, padx=16, pady=8)
        list_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(list_frame, text="Geplande acties", bg=self.BG, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.listbox = tk.Listbox(
            list_frame, height=6, font=("Consolas", 10),
            selectmode=tk.SINGLE, activestyle="none",
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=4)
        ttk.Button(list_frame, text="Verwijder geselecteerd", command=self._remove).pack(anchor=tk.W)
        self._update_action_fields()

    def _on_resize(self, event):
        if event.widget is self:
            self.status_label.configure(wraplength=max(200, self.winfo_width() - 40))

    def _on_unmap(self, event):
        if event.widget is self and self.state() == "iconic" and not self._in_tray:
            self.after(100, self._hide_to_tray)

    def _hide_to_tray(self):
        if self._in_tray or self.state() != "iconic":
            return
        self._in_tray = True
        self.withdraw()
        self._status("Draait op de achtergrond — open via het icoon naast de klok")

    def show_window(self):
        self._in_tray = False
        self.deiconify()
        self.lift()
        self.focus_force()

    def request_quit(self):
        self._on_close()

    def _on_close(self):
        if self.scheduler.running:
            ok = messagebox.askyesno(
                APP_NAME,
                "Er lopen nog geplande acties.\n\nWeet je zeker dat je wilt afsluiten?",
                icon="warning",
            )
            if not ok:
                return
        self._quit()

    def _quit(self):
        self.scheduler.stop()
        if self._tray:
            self._tray.stop()
        self.destroy()

    def _on_start_with_windows(self):
        if self.start_with_windows.get():
            self.autorun.set(True)
            self.start_in_tray.set(True)
        self._refresh_windows_autostart()
        self._save()

    def _on_start_in_tray(self):
        self._refresh_windows_autostart()
        self._save()

    def _refresh_windows_autostart(self, show_error: bool = True):
        try:
            set_windows_autostart(
                self.start_with_windows.get(),
                minimized=self.start_in_tray.get(),
            )
        except OSError as e:
            self.start_with_windows.set(False)
            if show_error:
                messagebox.showerror(
                    APP_NAME,
                    f"Kon Windows-opstart niet instellen:\n{e}",
                )

    def _apply_launch_behavior(self):
        if self._launch_minimized:
            self._in_tray = True
            self.withdraw()
            self._status("Draait op de achtergrond — open via het icoon naast de klok")
        if (
            self._from_windows
            and self.autorun.get()
            and self.clicks
            and not self.scheduler.running
        ):
            self._start()

    def _update_action_fields(self) -> None:
        is_key = self.action_type.get() == "key"
        if is_key:
            self.click_fields.pack_forget()
            self.key_fields.pack(fill=tk.X, before=self.form_btns)
        else:
            self.key_fields.pack_forget()
            self.click_fields.pack(fill=tk.X, before=self.form_btns)

    def _capture_key(self) -> None:
        if self._capturing_key:
            return
        self._capturing_key = True
        self._status("Druk een toets...")
        self.bind("<KeyPress>", self._on_key_capture, add="+")

    def _on_key_capture(self, event) -> None:
        if not self._capturing_key:
            return
        self._capturing_key = False
        self.unbind("<KeyPress>")
        self.key.set(keysym_to_name(event.keysym))
        self._status(f"Toets gekozen: {self.key.get()}")

    def _update_value_field(self) -> None:
        if self.mode.get() == "clock":
            self.val_label.configure(text="Tijdstip")
            self.val_hint.configure(
                text="Wanneer moet er geklikt worden? Formaat: uu:mm:ss (bijv. 14:30:00). "
                     "Is dat tijdstip al voorbij, dan morgen op dat moment."
            )
            if self.val.get() in ("", "3"):
                self.val.set(datetime.now().strftime("%H:%M:%S"))
        else:
            self.val_label.configure(text="Seconden")
            self.val_hint.configure(text="Aantal seconden wachten vóór deze klik.")
            if ":" in self.val.get():
                self.val.set("3")

    def _action_label(self, entry: dict) -> str:
        if entry.get("type", "click") == "key":
            action = f"toets {entry['key']}"
        else:
            action = "2x" if entry.get("double") else "klik"
            action = f"{action} ({entry['x']}, {entry['y']})"
        if entry.get("mode") == "clock":
            return f"om {entry['time']}  →  {action}"
        return f"{entry.get('delay', 0):g}s  →  {action}"

    def _pick_pos(self):
        x, y = get_cursor_pos()
        self.x.set(str(x))
        self.y.set(str(y))
        self._status(f"Positie: ({x}, {y})")

    def _add(self):
        is_key = self.action_type.get() == "key"
        try:
            if is_key:
                parse_key(self.key.get())
            else:
                int(self.x.get())
                int(self.y.get())
            if self.mode.get() == "delay":
                float(self.val.get().replace(",", "."))
            else:
                time_str = self.val.get().strip()
                parts = time_str.split(":")
                if len(parts) != 3:
                    raise ValueError
                h, m, s = map(int, parts)
                if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
                    raise ValueError
        except ValueError:
            if is_key:
                messagebox.showwarning(
                    "Invoer",
                    "Vul een geldige toets in, bijv. F6, Enter of A.",
                )
            elif self.mode.get() == "clock":
                messagebox.showwarning(
                    "Invoer",
                    "Vul een geldig tijdstip in, bijv. 14:30:00 (uur:minuut:seconde).",
                )
            else:
                messagebox.showwarning("Invoer", "Controleer seconden, X en Y.")
            return

        if is_key:
            key_name = keysym_to_name(self.key.get().strip())
            if self.mode.get() == "delay":
                entry = {
                    "type": "key",
                    "mode": "delay",
                    "delay": float(self.val.get().replace(",", ".")),
                    "key": key_name,
                }
            else:
                time_str = self.val.get().strip()
                h, m, s = map(int, time_str.split(":"))
                entry = {
                    "type": "key",
                    "mode": "clock",
                    "time": f"{h:02d}:{m:02d}:{s:02d}",
                    "key": key_name,
                }
        elif self.mode.get() == "delay":
            entry = {
                "mode": "delay",
                "delay": float(self.val.get().replace(",", ".")),
                "x": int(self.x.get()),
                "y": int(self.y.get()),
                "double": self.double.get(),
            }
        else:
            time_str = self.val.get().strip()
            h, m, s = map(int, time_str.split(":"))
            entry = {
                "mode": "clock",
                "time": f"{h:02d}:{m:02d}:{s:02d}",
                "x": int(self.x.get()),
                "y": int(self.y.get()),
                "double": self.double.get(),
            }

        self.clicks.append(entry)
        self.listbox.insert(tk.END, self._action_label(entry))
        self._save()

    def _remove(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        self.listbox.delete(sel[0])
        del self.clicks[sel[0]]
        self._save()

    def _start(self):
        if not self.clicks:
            messagebox.showinfo(APP_NAME, "Voeg eerst minimaal één actie toe.")
            return
        try:
            pause = float(self.pause.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Invoer", "Ongeldige pauze.")
            return
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self._save()
        self.scheduler.start(self.clicks, self.repeat.get(), pause)
        self._status("Gestart — je kunt minimaliseren naar het systeemvak")

    def _stop(self):
        self.scheduler.stop()

    def _done(self):
        self.after(0, lambda: (
            self.btn_start.configure(state=tk.NORMAL),
            self.btn_stop.configure(state=tk.DISABLED),
        ))

    def _status(self, text):
        self.after(0, lambda: self.status.set(text))

    def _save(self):
        data = {
            "clicks": self.clicks,
            "repeat": self.repeat.get(),
            "pause": self.pause.get(),
            "start_with_windows": self.start_with_windows.get(),
            "autorun": self.autorun.get(),
            "start_in_tray": self.start_in_tray.get(),
        }
        config_path().write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self):
        path = config_path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        self.clicks = data.get("clicks", [])
        self.repeat.set(data.get("repeat", False))
        self.pause.set(str(data.get("pause", "5")))
        self.start_with_windows.set(data.get("start_with_windows", False))
        self.autorun.set(data.get("autorun", False))
        self.start_in_tray.set(data.get("start_in_tray", False))
        self.listbox.delete(0, tk.END)
        for c in self.clicks:
            self.listbox.insert(tk.END, self._action_label(c))
        if self.start_with_windows.get():
            self._refresh_windows_autostart(show_error=False)


if __name__ == "__main__":
    App().mainloop()
