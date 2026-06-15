from __future__ import annotations
import math
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

from config import (
    DIRECTION_MIN_PX, SHAKE_WINDOW_MS, SHAKE_REVERSAL_COUNT,
    PINCH_MIN_DELTA, POINTER_MARGIN, SCROLL_GAIN, SCROLL_ACCEL,
    POINTER_GAIN, POINTER_ALPHA_MIN, POINTER_ALPHA_MAX, POINTER_ALPHA_DIST,
)

# MediaPipe landmark indices
WRIST = 0
THUMB_CMC = 1
THUMB_TIP, THUMB_IP = 4, 3
INDEX_TIP,  INDEX_MCP,  INDEX_PIP  = 8,  5,  6
MIDDLE_TIP, MIDDLE_MCP, MIDDLE_PIP = 12, 9,  10
RING_TIP,   RING_MCP,   RING_PIP   = 16, 13, 14
PINKY_TIP,  PINKY_MCP,  PINKY_PIP  = 20, 17, 18


@dataclass
class Gesture:
    name: str
    is_continuous: bool = False
    dx: float = 0.0
    dy: float = 0.0
    scale: float = 1.0
    x: float = 0.0
    y: float = 0.0


class GestureClassifier:
    def __init__(self, frame_w: int, frame_h: int,
                 screen_w: int = 0, screen_h: int = 0) -> None:
        self._w = frame_w
        self._h = frame_h
        self._screen_w = screen_w or frame_w
        self._screen_h = screen_h or frame_h
        self.last_states: dict[str, bool] = {}
        self._prev_wrist: Optional[tuple[float, float]] = None
        self._prev_index: Optional[tuple[float, float]] = None
        self._y_history: deque = deque()
        self._shake_last_fired: float = 0.0
        # 드래그: 검지+약지 펼침 유지 = 드래그 모드
        self._ring_dragging: bool = False
        self._prev_pinch_dist: Optional[float] = None
        self._prev_spread_dist: Optional[float] = None
        self._smooth_dx: float = 0.0
        self._smooth_dy: float = 0.0
        self._prev_raw_x: float = 0.0
        self._prev_raw_y: float = 0.0
        self.pointer_gain: float = POINTER_GAIN
        # 클릭 앵커: 소지 탭 전 안정된 위치 보존 (rolling 4-frame buffer)
        self._click_anchor_history: deque = deque(maxlen=4)
        # 소지 탭 감지: 포인팅 중 소지 폄(2~8프레임) 후 다시 접힘 → 클릭
        self._ptap_streak: int = 0
        self._rtap_prev_ext: bool = False
        self._rtap_streak: int = 0
        self._tap_prev_ext: bool = False
        self._tap_streak: int = 0

    def classify(self, hand_landmarks, handedness: str = 'Right') -> Optional[Gesture]:
        if hand_landmarks is None:
            self.last_states = {}
            self._prev_index = None
            if self._ring_dragging:
                self._ring_dragging = False
                self._ptap_streak = 0
                return Gesture('drag_end')
            return None

        lm = hand_landmarks.landmark
        states = self._finger_states(lm, handedness)
        self.last_states = states
        count = sum(states.values())
        wrist_px = self._pixel(lm[WRIST])

        # 드래그 안전 종료: 검지가 접히거나 중지가 올라온 경우
        if self._ring_dragging and (not states['index'] or states['middle']):
            self._ring_dragging = False
            self._ptap_streak = 0
            self._prev_index = None
            return Gesture('drag_end')

        dx, dy = 0.0, 0.0
        if self._prev_wrist:
            dx = wrist_px[0] - self._prev_wrist[0]
            dy = wrist_px[1] - self._prev_wrist[1]
        self._prev_wrist = wrist_px

        # ── 검지 포인팅 (중지 없음) — 소지로 클릭/드래그 ────────────────
        if states['index'] and not states['middle']:

            if states['pinky']:
                self._ptap_streak += 1

                if self._ring_dragging:
                    # 드래그 유지: 커서 이동
                    move_g = self._classify_pointer_move(lm)
                    if move_g:
                        return Gesture('drag_move', is_continuous=True,
                                       x=move_g.x, y=move_g.y)
                    return None

                if self._ptap_streak >= 5:
                    # 소지 홀드 (5프레임 이상): 드래그 시작
                    self._ring_dragging = True
                    return Gesture('drag_start')

                # 탭 판정 대기 중: 포인터 이동 유지
                result = self._classify_pointer_move(lm)
                self._click_anchor_history.append((self._smooth_dx, self._smooth_dy))
                return result

            # 소지 접힘
            if self._ring_dragging:
                # 소지 접음 → 드래그 종료
                self._ring_dragging = False
                self._ptap_streak = 0
                self._prev_index = None
                return Gesture('drag_end')

            if 2 <= self._ptap_streak <= 4:
                # 소지 단발 탭 (2~4프레임): 클릭
                anchor = self._click_anchor_history[0] if self._click_anchor_history \
                    else (self._smooth_dx, self._smooth_dy)
                self._click_anchor_history.clear()
                self._ptap_streak = 0
                self._prev_index = None
                return Gesture('pointer_click', x=anchor[0], y=anchor[1])

            self._ptap_streak = 0
            result = self._classify_pointer_move(lm)
            self._click_anchor_history.append((self._smooth_dx, self._smooth_dy))
            return result

        # 포인터 모드 벗어나면 소지 상태 리셋
        self._ptap_streak = 0
        self._prev_index = None

        # ── 주먹 (창 분할) ───────────────────────────────────────────────
        if count == 0:
            return self._classify_fist(dx, dy)

        # ── 검지+중지 (스크롤) ───────────────────────────────────────────
        if states['index'] and states['middle'] and not states['thumb']:
            if abs(dy) < 5:
                return None
            scroll = dy * SCROLL_GAIN * (1.0 + abs(dy) * SCROLL_ACCEL)
            return Gesture('scroll', is_continuous=True, dy=scroll)

        # 엄지+검지 (줌)
        if count == 2 and states['thumb'] and states['index'] and not states['middle']:
            return self._classify_pinch(lm)

        # ── 중지+약지+소지 (6분할) ──────────────────────────────────────
        if (count == 3 and states['middle'] and states['ring'] and states['pinky']
                and not states['thumb'] and not states['index']):
            return self._classify_rect_6split(wrist_px, dx, dy)

        # ── 4손가락 (데스크탑/미션컨트롤) ──────────────────────────────
        if count == 4 and not states['thumb']:
            return self._classify_4finger(dx, dy)

        # ── 5손가락 (런치패드/데스크탑 보기) ────────────────────────────
        if count == 5:
            return self._classify_5finger(lm)

        return None

    # ── 손가락 상태 ────────────────────────────────────────────────────

    def _finger_states(self, lm: list, handedness: str = 'Right') -> dict[str, bool]:
        # THUMB_CMC vs PINKY_MCP x 비교로 엄지 방향 기하학적 판단
        thumb_on_right = lm[THUMB_CMC].x > lm[PINKY_MCP].x
        thumb_extended = (lm[THUMB_TIP].x > lm[THUMB_IP].x if thumb_on_right
                          else lm[THUMB_TIP].x < lm[THUMB_IP].x)
        return {
            'thumb':  thumb_extended,
            'index':  lm[INDEX_TIP].y  < lm[INDEX_MCP].y,   # MCP: 포인팅 감지 쉽게
            'middle': lm[MIDDLE_TIP].y < lm[MIDDLE_MCP].y,  # MCP: 스크롤 감지 쉽게
            'ring':   lm[RING_TIP].y   < lm[RING_PIP].y,    # PIP: 드래그 오인식 방지
            'pinky':  lm[PINKY_TIP].y  < lm[PINKY_PIP].y,   # PIP: 클릭 오인식 방지
        }

    def _pixel(self, lm_point) -> tuple[float, float]:
        return (lm_point.x * self._w, lm_point.y * self._h)

    # ── 방향 / 흔들기 / 탭 감지 ────────────────────────────────────────

    def _direction(self, dx: float, dy: float) -> Optional[str]:
        if math.sqrt(dx ** 2 + dy ** 2) < DIRECTION_MIN_PX:
            return None
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        dirs = ['→', '↗', '↑', '↖', '←', '↙', '↓', '↘']
        return dirs[round(angle / 45) % 8]

    def _detect_shake(self, y_px: float) -> bool:
        now = time.monotonic() * 1000

        # 발동 후 1초 쿨다운
        if now - self._shake_last_fired < 1000:
            self._y_history.append((now, y_px))
            return False

        self._y_history.append((now, y_px))
        cutoff = now - SHAKE_WINDOW_MS
        while self._y_history and self._y_history[0][0] < cutoff:
            self._y_history.popleft()
        ys = [y for _, y in self._y_history]

        # 방향 전환 + 진폭 10px 이상인 경우만 reversal로 인정
        reversals = sum(
            1 for i in range(1, len(ys) - 1)
            if ((ys[i] - ys[i - 1]) * (ys[i + 1] - ys[i]) < 0
                and abs(ys[i] - ys[i - 1]) + abs(ys[i + 1] - ys[i]) > 10)
        )
        if reversals >= SHAKE_REVERSAL_COUNT:
            self._shake_last_fired = now
            self._y_history.clear()
            return True
        return False

    def _detect_tap(self, is_pointing: bool) -> bool:
        """검지 탭: 연속 2~10프레임 접힘 후 펼침."""
        if is_pointing:
            fired = self._tap_prev_ext and 2 <= self._tap_streak <= 10
            self._tap_streak = 0
            self._tap_prev_ext = True
            return fired
        else:
            if self._tap_prev_ext:
                self._tap_streak += 1
                if self._tap_streak > 10:
                    self._tap_prev_ext = False
                    self._tap_streak = 0
            return False

    def _detect_right_tap(self, both_extended: bool) -> bool:
        """검지+중지 탭: 연속 2~10프레임 접힘 후 펼침."""
        if both_extended:
            fired = self._rtap_prev_ext and 2 <= self._rtap_streak <= 10
            self._rtap_streak = 0
            self._rtap_prev_ext = True
            return fired
        else:
            if self._rtap_prev_ext:
                self._rtap_streak += 1
                if self._rtap_streak > 10:
                    self._rtap_prev_ext = False
                    self._rtap_streak = 0
            return False

    # ── 개별 제스처 분류 ────────────────────────────────────────────────

    def _active_zone(self) -> tuple[float, float, float, float]:
        """화면 비율에 맞는 활성 영역 (x0, y0, rect_w, rect_h) 반환.
        pointer_gain > 1 → 박스 작아짐(커서 빠름), < 1 → 커짐(느림)."""
        aspect = self._screen_w / self._screen_h
        max_w = self._w * (1 - 2 * POINTER_MARGIN) / self.pointer_gain
        max_h = self._h * (1 - 2 * POINTER_MARGIN) / self.pointer_gain
        if max_w / max_h > aspect:
            rect_h = max_h
            rect_w = rect_h * aspect
        else:
            rect_w = max_w
            rect_h = rect_w / aspect
        # 박스가 프레임 밖으로 나가지 않도록 클램핑
        rect_w = min(rect_w, self._w * 0.98)
        rect_h = min(rect_h, self._h * 0.98)
        x0 = (self._w - rect_w) / 2
        y0 = max(0.0, (self._h - rect_h) / 2)
        return x0, y0, rect_w, rect_h

    def _classify_pointer_move(self, lm: list) -> Optional[Gesture]:
        index_tip_px = self._pixel(lm[INDEX_TIP])
        x0, y0, active_w, active_h = self._active_zone()
        raw_x = max(0.0, min(1.0, (index_tip_px[0] - x0) / active_w))
        raw_y = max(0.0, min(1.0, (index_tip_px[1] - y0) / active_h))

        if self._prev_index is None:
            self._prev_index = index_tip_px
            self._prev_raw_x = raw_x
            self._prev_raw_y = raw_y
            self._smooth_dx = raw_x
            self._smooth_dy = raw_y
            return None

        self._prev_index = index_tip_px

        dx = raw_x - self._smooth_dx
        dy = raw_y - self._smooth_dy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0.002:
            t = min(1.0, dist / POINTER_ALPHA_DIST)
            alpha = POINTER_ALPHA_MIN + t * (POINTER_ALPHA_MAX - POINTER_ALPHA_MIN)
            self._smooth_dx = max(0.0, min(1.0, self._smooth_dx + dx * alpha))
            self._smooth_dy = max(0.0, min(1.0, self._smooth_dy + dy * alpha))

        return Gesture('pointer_move', is_continuous=True,
                       x=self._smooth_dx, y=self._smooth_dy)

    def _classify_fist(self, dx: float, dy: float) -> Optional[Gesture]:
        d = self._direction(dx, dy)
        if d is None:
            return None
        mapping = {
            '←': 'rect_left_half',  '→': 'rect_right_half',
            '↖': 'rect_top_left',   '↗': 'rect_top_right',
            '↙': 'rect_bottom_left', '↘': 'rect_bottom_right',
        }
        name = mapping.get(d)
        return Gesture(name) if name else None

    def _classify_pinch(self, lm: list) -> Optional[Gesture]:
        thumb_px = self._pixel(lm[THUMB_TIP])
        index_px = self._pixel(lm[INDEX_TIP])
        dist = math.sqrt((thumb_px[0] - index_px[0]) ** 2 + (thumb_px[1] - index_px[1]) ** 2)
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
            '←': 'rect_first_third',   '→': 'rect_last_third',
            '↑': 'rect_top_center',    '↓': 'rect_bottom_center',
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
            math.sqrt((self._pixel(lm[t])[0] - wrist_px[0]) ** 2 +
                      (self._pixel(lm[t])[1] - wrist_px[1]) ** 2)
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
