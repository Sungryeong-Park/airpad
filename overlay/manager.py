from typing import Optional
import numpy as np
from config import OVERLAY_LEVEL
from gesture.classifier import Gesture


class OverlayManager:
    def __init__(self) -> None:
        self.level: int = OVERLAY_LEVEL
        self._window = None
        if self.level >= 1:
            from overlay.window import OverlayWindow
            self._window = OverlayWindow()
            self._window.start()

    def show(self, gesture: Gesture, frame: Optional[np.ndarray] = None) -> None:
        if self.level == 0:
            return
        if self.level >= 1 and self._window:
            self._window.set_text(gesture.name)
        if self.level == 2 and frame is not None:
            self._show_landmarks(frame)

    def _show_landmarks(self, frame: np.ndarray) -> None:
        pass
