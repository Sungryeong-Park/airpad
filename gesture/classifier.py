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
        self._prev_spread_dist: Optional[float] = None

    def classify(self, hand_landmarks) -> Optional[Gesture]:
        if hand_landmarks is None:
            return None
        lm = hand_landmarks.landmark
        states = self._finger_states(lm)
        count = sum(states.values())
        wrist_px = self._pixel(lm[WRIST])

        dx, dy = 0.0, 0.0
        if self._prev_wrist:
            dx = wrist_px[0] - self._prev_wrist[0]
            dy = wrist_px[1] - self._prev_wrist[1]
        self._prev_wrist = wrist_px

        if self._detect_tap(states['index']):
            self._drag_anchor = None
            self._dragging = False
            return Gesture('pointer_click')
        if self._detect_right_tap(states['index'] and states['middle']):
            return Gesture('pointer_right_click')

        if count == 0:
            result = self._classify_drag(lm) if self._dragging or self._drag_anchor else self._classify_fist(dx, dy)
            return result
        if count == 1 and states['index']:
            return self._classify_pointer_move(lm)
        if count == 2 and states['index'] and states['middle'] and not states['thumb']:
            return Gesture('scroll', is_continuous=True, dx=dx, dy=dy)
        if count == 2 and states['thumb'] and states['index'] and not states['middle']:
            return self._classify_pinch(lm)
        if (count == 3 and states['middle'] and states['ring'] and states['pinky']
                and not states['thumb'] and not states['index']):
            return self._classify_rect_6split(wrist_px, dx, dy)
        if count == 4 and not states['thumb']:
            return self._classify_4finger(dx, dy)
        if count == 5:
            return self._classify_5finger(lm)
        return None

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
        if math.sqrt(dx ** 2 + dy ** 2) < DIRECTION_MIN_PX:
            return None
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        dirs = ['→', '↗', '↑', '↖', '←', '↙', '↓', '↘']
        return dirs[round(angle / 45) % 8]

    def _detect_shake(self, y_px: float) -> bool:
        now = time.monotonic() * 1000
        self._y_history.append((now, y_px))
        cutoff = now - SHAKE_WINDOW_MS
        while self._y_history and self._y_history[0][0] < cutoff:
            self._y_history.popleft()
        ys = [y for _, y in self._y_history]
        reversals = sum(
            1 for i in range(1, len(ys) - 1)
            if (ys[i] - ys[i - 1]) * (ys[i + 1] - ys[i]) < 0
        )
        return reversals >= SHAKE_REVERSAL_COUNT

    def _detect_tap(self, bent: bool) -> bool:
        self._tap_history.append(bent)
        if len(self._tap_history) < TAP_WINDOW_FRAMES:
            return False
        return (not self._tap_history[0]) and self._tap_history[-1]

    def _detect_right_tap(self, both_bent: bool) -> bool:
        self._rtap_history.append(both_bent)
        if len(self._rtap_history) < TAP_WINDOW_FRAMES:
            return False
        return (not self._rtap_history[0]) and self._rtap_history[-1]

    def _classify_fist(self, dx: float, dy: float) -> Optional[Gesture]:
        d = self._direction(dx, dy)
        if d is None:
            return None
        mapping = {
            '←': 'rect_left_half', '→': 'rect_right_half',
            '↖': 'rect_top_left',  '↗': 'rect_top_right',
            '↙': 'rect_bottom_left', '↘': 'rect_bottom_right',
        }
        name = mapping.get(d)
        return Gesture(name) if name else None

    def _classify_pinch(self, lm: list) -> Optional[Gesture]:
        thumb_px = self._pixel(lm[THUMB_TIP])
        index_px = self._pixel(lm[INDEX_TIP])
        dist = math.sqrt((thumb_px[0] - index_px[0])**2 + (thumb_px[1] - index_px[1])**2)
        if self._prev_pinch_dist is None:
            self._prev_pinch_dist = dist
            return None
        delta = dist - self._prev_pinch_dist
        self._prev_pinch_dist = dist
        if abs(delta) < PINCH_MIN_DELTA * max(self._w, self._h):
            return None
        scale = 1.0 + delta / max(self._w, self._h)
        return Gesture('zoom', is_continuous=True, scale=scale)

    def _classify_rect_6split(self, wrist_px: tuple, dx: float, dy: float) -> Optional[Gesture]:
        if self._detect_shake(wrist_px[1]):
            return Gesture('rect_center_third')
        d = self._direction(dx, dy)
        if d is None:
            return None
        mapping = {
            '←': 'rect_first_third',  '→': 'rect_last_third',
            '↑': 'rect_top_center',   '↓': 'rect_bottom_center',
            '↖': 'rect_top_left_sixth', '↗': 'rect_top_right_sixth',
            '↙': 'rect_bottom_left_sixth', '↘': 'rect_bottom_right_sixth',
        }
        name = mapping.get(d)
        return Gesture(name) if name else None

    def _classify_4finger(self, dx: float, dy: float) -> Optional[Gesture]:
        d = self._direction(dx, dy)
        if d is None:
            return None
        mapping = {
            '←': 'desktop_left', '→': 'desktop_right',
            '↑': 'mission_control', '↓': 'expose_close',
        }
        name = mapping.get(d)
        return Gesture(name) if name else None

    def _classify_5finger(self, lm: list) -> Optional[Gesture]:
        tips = [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
        wrist_px = self._pixel(lm[WRIST])
        spread = sum(
            math.sqrt((self._pixel(lm[t])[0] - wrist_px[0])**2 +
                      (self._pixel(lm[t])[1] - wrist_px[1])**2)
            for t in tips
        ) / len(tips)
        if self._prev_spread_dist is None:
            self._prev_spread_dist = spread
            return None
        delta = spread - self._prev_spread_dist
        self._prev_spread_dist = spread
        threshold = PINCH_MIN_DELTA * max(self._w, self._h)
        if delta < -threshold:
            return Gesture('launchpad')
        if delta > threshold:
            return Gesture('show_desktop')
        return None

    def _classify_pointer_move(self, lm: list) -> Optional[Gesture]:
        index_tip_px = self._pixel(lm[INDEX_TIP])

        if not self._dragging:
            if self._prev_index is not None:
                dx = index_tip_px[0] - self._prev_index[0]
                dy = index_tip_px[1] - self._prev_index[1]
                self._prev_index = index_tip_px
                return Gesture('pointer_move', is_continuous=True, dx=dx, dy=dy)
            self._prev_index = index_tip_px
            return None

        self._dragging = False
        self._drag_anchor = None
        self._prev_index = None
        return Gesture('drag_end')

    def _classify_drag(self, lm: list) -> Optional[Gesture]:
        index_tip_px = self._pixel(lm[INDEX_TIP])

        if self._drag_anchor is None:
            self._drag_anchor = index_tip_px
            self._prev_index = index_tip_px
            return None

        dist = math.sqrt((index_tip_px[0] - self._drag_anchor[0])**2 +
                         (index_tip_px[1] - self._drag_anchor[1])**2)
        if not self._dragging and dist > DRAG_MIN_PX:
            self._dragging = True
            self._prev_index = index_tip_px
            return Gesture('drag_start')
        if self._dragging and self._prev_index is not None:
            dx = index_tip_px[0] - self._prev_index[0]
            dy = index_tip_px[1] - self._prev_index[1]
            self._prev_index = index_tip_px
            return Gesture('drag_move', is_continuous=True, dx=dx, dy=dy)

        self._prev_index = index_tip_px
        return None
