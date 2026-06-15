import subprocess
from pynput.keyboard import Controller, Key

_kb = Controller()


def _hotkey(*keys) -> None:
    for k in keys:
        _kb.press(k)
    for k in reversed(keys):
        _kb.release(k)


def mission_control() -> None:
    _hotkey(Key.ctrl, Key.up)


def desktop_left() -> None:
    _hotkey(Key.ctrl, Key.left)


def desktop_right() -> None:
    _hotkey(Key.ctrl, Key.right)


def expose_close() -> None:
    _hotkey(Key.ctrl, Key.down)


def launchpad() -> None:
    subprocess.Popen(
        ['osascript', '-e', 'tell application "Launchpad" to activate'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def show_desktop() -> None:
    _hotkey(Key.cmd, Key.f3)
