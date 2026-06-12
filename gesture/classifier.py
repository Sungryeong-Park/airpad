from __future__ import annotations
import math
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from config import (
    DIRECTION_MIN_PX, SHAKE_WINDOW_MS, SHAKE_REVERSAL_COUNT,
    TAP_WINDOW_FRAMES, DRAG_MIN_PX, PINCH_MIN_DELTA,
)

# MediaPipe landmark indices
WRIST = 0
THUMB_TIP, THUMB_IP = 4, 3
INDEX_TIP, INDEX_MCP = 8, 5
MIDDLE_TIP, MIDDLE_MCP = 12, 9
RING_TIP, RING_MCP = 16, 13
PINKY_TIP, PINKY_MCP = 20, 17


@dataclass
class Gesture:
    name: str
    is_continuous: bool = False
    dx: float = 0.0
    dy: float = 0.0
    scale: float = 1.0


class GestureClassifier:
    def __init__(self, frame_w: int, frame_h: int) -> None:
        self._w = frame_w
        self._h = frame_h
        self._prev_wrist: Optional[tuple[float, float]] = None
        self._prev_index: Optional[tuple[float, float]] = None
        self._y_history: deque = deque()
        self._tap_history: deque = deque(maxlen=TAP_WINDOW_FRAMES)
        self._rtap_history: deque = deque(maxlen=TAP_WINDOW_FRAMES)
        self._drag_anchor: Optional[tuple[float, float]] = None
        self._dragging: bool = False
        self._prev_pinch_dist: Optional[float] = None

    def classify(self, hand_landmarks) -> Optional[Gesture]:
        raise NotImplementedError

    def _finger_states(self, lm: list) -> dict[str, bool]:
        return {
            'thumb':  lm[THUMB_TIP].x > lm[THUMB_IP].x,
            'index':  lm[INDEX_TIP].y < lm[INDEX_MCP].y,
            'middle': lm[MIDDLE_TIP].y < lm[MIDDLE_MCP].y,
            'ring':   lm[RING_TIP].y < lm[RING_MCP].y,
            'pinky':  lm[PINKY_TIP].y < lm[PINKY_MCP].y,
        }

    def _pixel(self, lm_point) -> tuple[float, float]:
        return (lm_point.x * self._w, lm_point.y * self._h)

    def _direction(self, dx: float, dy: float) -> Optional[str]:
        raise NotImplementedError

    def _detect_shake(self, y_px: float) -> bool:
        raise NotImplementedError

    def _detect_tap(self, bent: bool) -> bool:
        raise NotImplementedError

    def _detect_right_tap(self, both_bent: bool) -> bool:
        raise NotImplementedError
