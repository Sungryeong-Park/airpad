"""Transparent tkinter overlay window for gesture feedback."""
import tkinter as tk
import threading
from typing import Optional


class OverlayWindow:
    def __init__(self) -> None:
        self._root: Optional[tk.Tk] = None
        self._label: Optional[tk.Label] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes('-topmost', True)
        self._root.attributes('-alpha', 0.75)
        self._root.configure(bg='black')
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry(f'200x40+{sw - 220}+{sh - 60}')
        self._label = tk.Label(
            self._root, text='', fg='white', bg='black',
            font=('Helvetica', 14)
        )
        self._label.pack(expand=True)
        self._root.mainloop()

    def set_text(self, text: str) -> None:
        if self._label and self._root:
            self._root.after(0, lambda: self._label.config(text=text))

    def destroy(self) -> None:
        if self._root:
            self._root.after(0, self._root.destroy)
