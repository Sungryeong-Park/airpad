from unittest.mock import MagicMock
from gesture.classifier import GestureClassifier

WRIST = 0
THUMB_TIP, THUMB_IP = 4, 3
INDEX_TIP, INDEX_MCP = 8, 5
MIDDLE_TIP, MIDDLE_MCP = 12, 9
RING_TIP, RING_MCP = 16, 13
PINKY_TIP, PINKY_MCP = 20, 17


def make_lm(positions: dict) -> list:
    """Build 21 mock MediaPipe landmarks. positions: {idx: (x, y, z)}"""
    lms = []
    for i in range(21):
        m = MagicMock()
        x, y, z = positions.get(i, (0.5, 0.5, 0.0))
        m.x, m.y, m.z = x, y, z
        lms.append(m)
    return lms


def clf() -> GestureClassifier:
    return GestureClassifier(320, 240)
