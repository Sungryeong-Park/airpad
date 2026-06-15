from gesture.classifier import Gesture
from action import trackpad, system_gestures, rectangle, pointer


_DISPATCH: dict = {
    # Trackpad
    'scroll':         lambda g: trackpad.scroll(g.dx, g.dy),
    'zoom':           lambda g: trackpad.zoom(g.scale),
    # System
    'mission_control': lambda g: system_gestures.mission_control(),
    'desktop_left':    lambda g: system_gestures.desktop_left(),
    'desktop_right':   lambda g: system_gestures.desktop_right(),
    'expose_close':    lambda g: system_gestures.expose_close(),
    'launchpad':       lambda g: system_gestures.launchpad(),
    'show_desktop':    lambda g: system_gestures.show_desktop(),
    # Rectangle 2-split
    'rect_left_half':  lambda g: rectangle.left_half(),
    'rect_right_half': lambda g: rectangle.right_half(),
    # Rectangle 4-split
    'rect_top_left':    lambda g: rectangle.top_left(),
    'rect_top_right':   lambda g: rectangle.top_right(),
    'rect_bottom_left': lambda g: rectangle.bottom_left(),
    'rect_bottom_right':lambda g: rectangle.bottom_right(),
    # Rectangle 6-split thirds
    'rect_first_third':  lambda g: rectangle.first_third(),
    'rect_last_third':   lambda g: rectangle.last_third(),
    'rect_center_third': lambda g: rectangle.center_third(),
    # Rectangle 6-split sixths
    'rect_top_center':        lambda g: rectangle.top_center_sixth(),
    'rect_bottom_center':     lambda g: rectangle.bottom_center_sixth(),
    'rect_top_left_sixth':    lambda g: rectangle.top_left_sixth(),
    'rect_top_right_sixth':   lambda g: rectangle.top_right_sixth(),
    'rect_bottom_left_sixth': lambda g: rectangle.bottom_left_sixth(),
    'rect_bottom_right_sixth':lambda g: rectangle.bottom_right_sixth(),
    # Pointer
    'pointer_move':        lambda g: pointer.move(g.dx, g.dy),
    'pointer_click':       lambda g: (pointer.move_absolute(g.x, g.y), pointer.left_click()),
    'pointer_right_click': lambda g: pointer.right_click(),
    'drag_start':          lambda g: pointer.drag_start(),
    'drag_move':           lambda g: pointer.drag_move_absolute(g.x, g.y),
    'drag_end':            lambda g: pointer.drag_end(),
}


def execute(gesture: Gesture) -> None:
    fn = _DISPATCH.get(gesture.name)
    if fn:
        fn(gesture)
