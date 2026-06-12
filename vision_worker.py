"""Vision subprocess: camera capture → MediaPipe → classify → execute."""
import multiprocessing
import os
import time
from typing import Optional

import av
import mediapipe as mp
import numpy as np

from config import CAMERA_RESOLUTION, CAMERA_FPS, MEDIAPIPE_MODEL, PROCESS_NICE
from gesture.classifier import GestureClassifier
from action.executor import execute
from overlay.manager import OverlayManager


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
    classifier = GestureClassifier(w, h)
    overlay = OverlayManager()
    container: Optional[av.container.InputContainer] = None
    active = False

    while True:
        try:
            msg = queue.get_nowait()
            if msg == 'toggle':
                active = not active
                if active:
                    container = _open_camera(w, h, CAMERA_FPS)
                else:
                    if container:
                        container.close()
                    container = None
                    classifier = GestureClassifier(w, h)
        except Exception:
            pass

        if not active or container is None:
            time.sleep(0.05)
            continue

        frame_rgb = _next_frame(container, w, h)
        if frame_rgb is None:
            continue

        results = hands.process(frame_rgb)
        hand = (results.multi_hand_landmarks[0]
                if results.multi_hand_landmarks else None)

        gesture = classifier.classify(hand)
        if gesture:
            execute(gesture)
            overlay.show(gesture, frame_rgb if overlay.level == 2 else None)


def _open_camera(w: int, h: int, fps: int) -> av.container.InputContainer:
    container = av.open(
        'avfoundation',
        format='avfoundation',
        options={
            'video_size': f'{w}x{h}',
            'framerate': str(fps),
            'pixel_format': 'yuyv422',
        },
    )
    return container


def _next_frame(container: av.container.InputContainer,
                w: int, h: int) -> Optional[np.ndarray]:
    try:
        for packet in container.demux(video=0):
            for frame in packet.decode():
                arr = frame.to_ndarray(format='rgb24')
                return arr
    except Exception:
        return None
    return None
