import Quartz
from config import CAMERA_RESOLUTION


def scroll(dx: float, dy: float) -> None:
    event = Quartz.CGEventCreateScrollWheelEvent(
        None,
        Quartz.kCGScrollEventUnitPixel,
        2,
        int(dy),
        int(dx),
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def zoom(scale: float) -> None:
    amount = int((scale - 1.0) * 50)
    if amount == 0:
        return
    event = Quartz.CGEventCreateScrollWheelEvent(
        None,
        Quartz.kCGScrollEventUnitPixel,
        1,
        amount,
    )
    Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskAlternate)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
