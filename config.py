from __future__ import annotations

from dotenv import load_dotenv
import os

load_dotenv()

CAMERA_RESOLUTION: tuple[int, int] = (320, 240)
CAMERA_INDEX: int = int(os.getenv("CAMERA_INDEX", "0"))
CAMERA_FPS: int = int(os.getenv("CAMERA_FPS", "30"))
MEDIAPIPE_MODEL: str = os.getenv("MEDIAPIPE_MODEL", "lite")
HOTKEY: str = os.getenv("HOTKEY", "<ctrl>+<space>")
OVERLAY_LEVEL: int = int(os.getenv("OVERLAY_LEVEL", "0"))
PROCESS_NICE: int = int(os.getenv("PROCESS_NICE", "10"))

DIRECTION_MIN_PX: float = float(os.getenv("DIRECTION_MIN_PX", "15"))
POINTER_MARGIN: float = float(os.getenv("POINTER_MARGIN", "0.37"))  # 활성 영역 마진 (각 측 37%)
POINTER_GAIN: float = float(os.getenv("POINTER_GAIN", "0.35"))       # 커서 속도 배율 (낮을수록 느림)
POINTER_ALPHA_MIN: float = float(os.getenv("POINTER_ALPHA_MIN", "0.08"))  # 정지 시 EMA alpha (낮을수록 노이즈 흡수)
POINTER_ALPHA_MAX: float = float(os.getenv("POINTER_ALPHA_MAX", "0.90"))  # 이동 시 EMA alpha (높을수록 빠른 추적)
POINTER_ALPHA_DIST: float = float(os.getenv("POINTER_ALPHA_DIST", "0.06"))  # alpha 최대에 도달하는 거리
SCROLL_GAIN: float = float(os.getenv("SCROLL_GAIN", "0.3"))    # 중립점 오프셋 → 스크롤 속도
SCROLL_ACCEL: float = float(os.getenv("SCROLL_ACCEL", "0.06")) # 멀수록 가속 계수
SHAKE_WINDOW_MS: int = int(os.getenv("SHAKE_WINDOW_MS", "600"))
SHAKE_REVERSAL_COUNT: int = 2
TAP_WINDOW_FRAMES: int = int(os.getenv("TAP_WINDOW_FRAMES", "3"))
DRAG_MIN_PX: float = float(os.getenv("DRAG_MIN_PX", "15"))
PINCH_MIN_DELTA: float = float(os.getenv("PINCH_MIN_DELTA", "0.04"))
