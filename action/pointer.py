import Quartz


def _current_pos() -> tuple[float, float]:
    loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    return loc.x, loc.y


def _screen_size() -> tuple[int, int]:
    display = Quartz.CGMainDisplayID()
    return Quartz.CGDisplayPixelsWide(display), Quartz.CGDisplayPixelsHigh(display)


def move_absolute(norm_x: float, norm_y: float) -> None:
    sw, sh = _screen_size()
    pt = Quartz.CGPointMake(norm_x * sw, norm_y * sh)
    event = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, pt, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def move(dx: float, dy: float) -> None:
    x, y = _current_pos()
    pt = Quartz.CGPointMake(x + dx, y + dy)
    event = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, pt, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def left_click() -> None:
    x, y = _current_pos()
    pt = Quartz.CGPointMake(x, y)
    for etype in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        e = Quartz.CGEventCreateMouseEvent(None, etype, pt, Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def right_click() -> None:
    x, y = _current_pos()
    pt = Quartz.CGPointMake(x, y)
    for etype in (Quartz.kCGEventRightMouseDown, Quartz.kCGEventRightMouseUp):
        e = Quartz.CGEventCreateMouseEvent(None, etype, pt, Quartz.kCGMouseButtonRight)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def drag_start() -> None:
    x, y = _current_pos()
    pt = Quartz.CGPointMake(x, y)
    e = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def drag_move_absolute(norm_x: float, norm_y: float) -> None:
    sw, sh = _screen_size()
    pt = Quartz.CGPointMake(norm_x * sw, norm_y * sh)
    e = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDragged, pt, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)


def drag_end() -> None:
    x, y = _current_pos()
    pt = Quartz.CGPointMake(x, y)
    e = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, pt, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, e)
