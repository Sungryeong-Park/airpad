"""Vision subprocess: camera capture → MediaPipe → classify → execute."""
import multiprocessing
import os
import threading
import time
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
import Quartz
from pynput import keyboard

from config import CAMERA_RESOLUTION, CAMERA_INDEX, CAMERA_FPS, MEDIAPIPE_MODEL, PROCESS_NICE
from gesture.classifier import GestureClassifier
from action.executor import execute
from overlay.manager import OverlayManager


def _print_gain(gain: float, direction: str) -> None:
    filled = int((gain - 0.05) / 1.95 * 20)
    bar = '█' * filled + '░' * (20 - filled)
    print(f'[DPI] {direction}  [{bar}]  {gain:.2f}  (↑빠름 / ↓느림)', flush=True)


def run(queue: multiprocessing.Queue) -> None:
    os.nice(PROCESS_NICE)

    model_complexity = 0 if MEDIAPIPE_MODEL == 'lite' else 1
    hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=model_complexity,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    )

    w, h = CAMERA_RESOLUTION
    _display = Quartz.CGMainDisplayID()
    _sw = Quartz.CGDisplayPixelsWide(_display)
    _sh = Quartz.CGDisplayPixelsHigh(_display)
    classifier = GestureClassifier(w, h, _sw, _sh)

    def _on_key(key):
        try:
            if key == keyboard.Key.up:
                classifier.pointer_gain = min(2.0, round(classifier.pointer_gain + 0.05, 2))
                _print_gain(classifier.pointer_gain, '↑')
            elif key == keyboard.Key.down:
                classifier.pointer_gain = max(0.05, round(classifier.pointer_gain - 0.05, 2))
                _print_gain(classifier.pointer_gain, '↓')
        except AttributeError:
            pass

    keyboard.Listener(on_press=_on_key, daemon=True).start()
    overlay = OverlayManager()
    cap: Optional[cv2.VideoCapture] = None
    capture: Optional[_LatestFrame] = None
    active = False

    while True:
        try:
            msg = queue.get_nowait()
            if msg == 'toggle':
                active = not active
                if active:
                    try:
                        cap = _open_camera(w, h, CAMERA_FPS)
                        capture = _LatestFrame(cap)
                        print('[airpad] 카메라 열기 성공', flush=True)
                    except Exception as e:
                        print(f'[airpad] 카메라 열기 실패: {e}', flush=True)
                        active = False
                else:
                    if cap:
                        cap.release()
                    cap = None
                    capture = None
                    classifier = GestureClassifier(w, h, _sw, _sh)
        except Exception:
            pass

        if not active or capture is None:
            time.sleep(0.05)
            continue

        frame_rgb = capture.read()
        if frame_rgb is None:
            time.sleep(0.005)
            continue

        results = hands.process(frame_rgb)
        hand = None
        handedness = 'Right'
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            if results.multi_handedness:
                handedness = results.multi_handedness[0].classification[0].label

        gesture = classifier.classify(hand, handedness)
        if gesture:
            execute(gesture)
            overlay.show(gesture, frame_rgb if overlay.level == 2 else None)

        preview = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        if hand:
            mp.solutions.drawing_utils.draw_landmarks(
                preview, hand, mp.solutions.hands.HAND_CONNECTIONS)
        cv2.imshow('Airpad', preview)
        cv2.waitKey(1)


class _LatestFrame:
    """캡처 전용 스레드 — 항상 최신 프레임만 유지해 mediapipe 처리 중 버퍼 밀림 방지."""

    def __init__(self, cap: cv2.VideoCapture) -> None:
        self._cap = cap
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        while True:
            ret, frame = self._cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                with self._lock:
                    self._frame = rgb

    def read(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frame


def _open_camera(w: int, h: int, fps: int) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        raise RuntimeError('카메라를 열 수 없습니다.')
    return cap
