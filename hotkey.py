"""Listens for the global toggle hotkey and sends signal via queue."""
import multiprocessing
from pynput import keyboard
from config import HOTKEY


def start(queue: multiprocessing.Queue) -> None:
    def on_activate():
        queue.put('toggle')

    with keyboard.GlobalHotKeys({HOTKEY: on_activate}) as listener:
        listener.join()
