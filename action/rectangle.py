from pynput.keyboard import Controller, Key, KeyCode

_kb = Controller()


def _rect(*keys) -> None:
    for k in keys:
        _kb.press(k)
    for k in reversed(keys):
        _kb.release(k)


# 2-split
def left_half() -> None:      _rect(Key.ctrl, Key.alt, Key.left)
def right_half() -> None:     _rect(Key.ctrl, Key.alt, Key.right)

# 4-split
def top_left() -> None:       _rect(Key.ctrl, Key.alt, KeyCode.from_char('u'))
def top_right() -> None:      _rect(Key.ctrl, Key.alt, KeyCode.from_char('i'))
def bottom_left() -> None:    _rect(Key.ctrl, Key.alt, KeyCode.from_char('j'))
def bottom_right() -> None:   _rect(Key.ctrl, Key.alt, KeyCode.from_char('k'))

# 6-split (thirds)
def first_third() -> None:    _rect(Key.ctrl, Key.alt, KeyCode.from_char('d'))
def last_third() -> None:     _rect(Key.ctrl, Key.alt, KeyCode.from_char('g'))
def center_third() -> None:   _rect(Key.ctrl, Key.alt, KeyCode.from_char('f'))

# 6-split (sixths)
def top_left_sixth() -> None:      _rect(Key.ctrl, Key.alt, KeyCode.from_char('l'))
def top_center_sixth() -> None:    _rect(Key.ctrl, Key.alt, KeyCode.from_char(';'))
def top_right_sixth() -> None:     _rect(Key.ctrl, Key.alt, KeyCode.from_char("'"))
def bottom_left_sixth() -> None:   _rect(Key.ctrl, Key.alt, KeyCode.from_char(','))
def bottom_center_sixth() -> None: _rect(Key.ctrl, Key.alt, KeyCode.from_char('.'))
def bottom_right_sixth() -> None:  _rect(Key.ctrl, Key.alt, KeyCode.from_char('/'))
