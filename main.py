"""
MouseClick — simuleer muisklikken op instelbare tijden en posities (Windows).
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
    messagebox.showerror("MouseClick", "Deze app werkt alleen op Windows.")
    sys.exit(1)

from mouse_click import click, get_cursor_pos


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
                    self.set_status(f"Klik {i + 1}/{len(clicks)} → ({c['x']}, {c['y']})")
                    click(c["x"], c["y"])
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
        self.title("MouseClick")
        self.geometry("420x520")
        self.configure(bg=self.BG)
        self.resizable(False, False)

        self.clicks: list[dict] = []
        self.scheduler = Scheduler(self._status, self._done)
        self._build()
        self._load()

    def _build(self):
        pad = {"padx": 16, "pady": 4}

        header = tk.Label(
            self, text="MouseClick", font=("Segoe UI", 18, "bold"),
            bg=self.BG, fg="#111",
        )
        header.pack(pady=(16, 2))
        tk.Label(
            self, text="Plan muisklikken op tijd en positie",
            font=("Segoe UI", 10), bg=self.BG, fg="#555",
        ).pack(pady=(0, 12))

        form = tk.Frame(self, bg="white", highlightbackground="#ddd", highlightthickness=1)
        form.pack(fill=tk.X, padx=16, pady=4)

        inner = tk.Frame(form, bg="white", padx=12, pady=12)
        inner.pack(fill=tk.X)

        self.mode = tk.StringVar(value="delay")
        mode_row = tk.Frame(inner, bg="white")
        mode_row.pack(fill=tk.X, pady=(0, 8))
        tk.Label(mode_row, text="Timing", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        ttk.Radiobutton(mode_row, text="Vertraging (sec)", variable=self.mode, value="delay").pack(anchor=tk.W)
        ttk.Radiobutton(mode_row, text="Kloktijd (HH:MM:SS)", variable=self.mode, value="clock").pack(anchor=tk.W)

        self.val = tk.StringVar(value="3")
        row1 = tk.Frame(inner, bg="white")
        row1.pack(fill=tk.X, pady=4)
        tk.Label(row1, text="Waarde", bg="white", width=8, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.val, width=28).pack(side=tk.LEFT)

        self.x = tk.StringVar(value="500")
        self.y = tk.StringVar(value="400")
        row2 = tk.Frame(inner, bg="white")
        row2.pack(fill=tk.X, pady=4)
        tk.Label(row2, text="X", bg="white", width=8, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.x, width=10).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(row2, text="Y", bg="white").pack(side=tk.LEFT, padx=(0, 4))
        ttk.Entry(row2, textvariable=self.y, width=10).pack(side=tk.LEFT)

        btns = tk.Frame(inner, bg="white")
        btns.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btns, text="Huidige positie", command=self._pick_pos).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(btns, text="+ Toevoegen", command=self._add).pack(side=tk.LEFT)

        list_frame = tk.Frame(self, bg=self.BG)
        list_frame.pack(fill=tk.BOTH, expand=True, **pad)
        tk.Label(list_frame, text="Geplande klikken", bg=self.BG, font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self.listbox = tk.Listbox(
            list_frame, height=8, font=("Consolas", 10),
            selectmode=tk.SINGLE, activestyle="none",
        )
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=4)
        ttk.Button(list_frame, text="Verwijder geselecteerd", command=self._remove).pack(anchor=tk.W)

        opts = tk.Frame(self, bg=self.BG)
        opts.pack(fill=tk.X, padx=16)
        self.repeat = tk.BooleanVar()
        ttk.Checkbutton(opts, text="Herhalen", variable=self.repeat).pack(side=tk.LEFT)
        tk.Label(opts, text="Pauze (sec)", bg=self.BG).pack(side=tk.LEFT, padx=(12, 4))
        self.pause = tk.StringVar(value="5")
        ttk.Entry(opts, textvariable=self.pause, width=5).pack(side=tk.LEFT)

        ctrl = tk.Frame(self, bg=self.BG)
        ctrl.pack(fill=tk.X, padx=16, pady=12)

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

        self.status = tk.StringVar(value="Gereed — voeg klikken toe en druk op Start")
        tk.Label(
            self, textvariable=self.status, bg=self.BG, fg="#555",
            font=("Segoe UI", 9), wraplength=380,
        ).pack(pady=(0, 12))

    def _pick_pos(self):
        x, y = get_cursor_pos()
        self.x.set(str(x))
        self.y.set(str(y))
        self._status(f"Positie: ({x}, {y})")

    def _add(self):
        try:
            x, y = int(self.x.get()), int(self.y.get())
            if self.mode.get() == "delay":
                float(self.val.get().replace(",", "."))
                entry = {"mode": "delay", "delay": float(self.val.get().replace(",", ".")), "x": x, "y": y}
                label = f"{entry['delay']:g}s  →  ({x}, {y})"
            else:
                parts = self.val.get().strip().split(":")
                if len(parts) != 3:
                    raise ValueError
                entry = {"mode": "clock", "time": self.val.get().strip(), "x": x, "y": y}
                label = f"{entry['time']}  →  ({x}, {y})"
        except ValueError:
            messagebox.showwarning("Invoer", "Controleer waarde, X en Y.")
            return
        self.clicks.append(entry)
        self.listbox.insert(tk.END, label)
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
            messagebox.showinfo("MouseClick", "Voeg eerst minimaal één klik toe.")
            return
        try:
            pause = float(self.pause.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Invoer", "Ongeldige pauze.")
            return
        self.btn_start.configure(state=tk.DISABLED)
        self.btn_stop.configure(state=tk.NORMAL)
        self.scheduler.start(self.clicks, self.repeat.get(), pause)

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
        data = {"clicks": self.clicks, "repeat": self.repeat.get(), "pause": self.pause.get()}
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
        self.listbox.delete(0, tk.END)
        for c in self.clicks:
            if c.get("mode") == "clock":
                self.listbox.insert(tk.END, f"{c['time']}  →  ({c['x']}, {c['y']})")
            else:
                self.listbox.insert(tk.END, f"{c.get('delay', 0):g}s  →  ({c['x']}, {c['y']})")


if __name__ == "__main__":
    App().mainloop()
