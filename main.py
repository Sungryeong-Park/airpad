"""Entry point: rumps menu bar app + vision subprocess."""
import multiprocessing
import os
import sys

import rumps

from config import HOTKEY
import hotkey
import vision_worker


class AirpadApp(rumps.App):
    def __init__(self, queue: multiprocessing.Queue) -> None:
        super().__init__('🤚', quit_button='종료')
        self._queue = queue
        self._active = False

    @rumps.clicked('활성화/비활성화')
    def toggle_menu(self, _) -> None:
        self._toggle()

    def _toggle(self) -> None:
        self._active = not self._active
        self.title = '✋' if self._active else '🤚'
        self._queue.put('toggle')


def main() -> None:
    queue: multiprocessing.Queue = multiprocessing.Queue()

    proc = multiprocessing.Process(target=vision_worker.run, args=(queue,), daemon=True)
    proc.start()

    import threading
    hotkey_thread = threading.Thread(target=hotkey.start, args=(queue,), daemon=True)
    hotkey_thread.start()

    app = AirpadApp(queue)
    app.menu = ['활성화/비활성화']
    app.run()


if __name__ == '__main__':
    main()
