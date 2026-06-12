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


def test_index_extended_when_tip_above_mcp():
    c = clf()
    lms = make_lm({INDEX_TIP: (0.5, 0.2, 0), INDEX_MCP: (0.5, 0.6, 0)})
    assert c._finger_states(lms)['index'] is True

def test_index_curled_when_tip_below_mcp():
    c = clf()
    lms = make_lm({INDEX_TIP: (0.5, 0.75, 0), INDEX_MCP: (0.5, 0.5, 0)})
    assert c._finger_states(lms)['index'] is False

def test_all_fingers_extended():
    c = clf()
    lms = make_lm({
        THUMB_TIP: (0.8, 0.5, 0), THUMB_IP: (0.6, 0.5, 0),
        INDEX_TIP: (0.5, 0.1, 0), INDEX_MCP: (0.5, 0.5, 0),
        MIDDLE_TIP: (0.5, 0.1, 0), MIDDLE_MCP: (0.5, 0.5, 0),
        RING_TIP: (0.5, 0.1, 0), RING_MCP: (0.5, 0.5, 0),
        PINKY_TIP: (0.5, 0.1, 0), PINKY_MCP: (0.5, 0.5, 0),
    })
    states = c._finger_states(lms)
    assert all(states.values())

def test_fist_all_curled():
    c = clf()
    lms = make_lm({
        THUMB_TIP: (0.5, 0.5, 0), THUMB_IP: (0.6, 0.5, 0),
        INDEX_TIP: (0.5, 0.75, 0), INDEX_MCP: (0.5, 0.5, 0),
        MIDDLE_TIP: (0.5, 0.75, 0), MIDDLE_MCP: (0.5, 0.5, 0),
        RING_TIP: (0.5, 0.75, 0), RING_MCP: (0.5, 0.5, 0),
        PINKY_TIP: (0.5, 0.75, 0), PINKY_MCP: (0.5, 0.5, 0),
    })
    states = c._finger_states(lms)
    assert not any(states.values())
