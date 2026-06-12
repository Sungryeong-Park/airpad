from __future__ import annotations

from dotenv import load_dotenv
import os

load_dotenv()

CAMERA_RESOLUTION: tuple[int, int] = (320, 240)
CAMERA_FPS: int = int(os.getenv("CAMERA_FPS", "15"))
MEDIAPIPE_MODEL: str = os.getenv("MEDIAPIPE_MODEL", "lite")
HOTKEY: str = os.getenv("HOTKEY", "<ctrl>+<space>")
OVERLAY_LEVEL: int = int(os.getenv("OVERLAY_LEVEL", "0"))
PROCESS_NICE: int = int(os.getenv("PROCESS_NICE", "10"))

DIRECTION_MIN_PX: float = float(os.getenv("DIRECTION_MIN_PX", "30"))
SHAKE_WINDOW_MS: int = int(os.getenv("SHAKE_WINDOW_MS", "600"))
SHAKE_REVERSAL_COUNT: int = 2
TAP_WINDOW_FRAMES: int = int(os.getenv("TAP_WINDOW_FRAMES", "3"))
DRAG_MIN_PX: float = float(os.getenv("DRAG_MIN_PX", "15"))
PINCH_MIN_DELTA: float = float(os.getenv("PINCH_MIN_DELTA", "0.04"))
