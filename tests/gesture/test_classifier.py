from unittest.mock import MagicMock
from gesture.classifier import GestureClassifier

WRIST = 0
THUMB_CMC = 1
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
        THUMB_CMC: (0.8, 0.5, 0), THUMB_TIP: (0.9, 0.5, 0), THUMB_IP: (0.7, 0.5, 0),
        INDEX_TIP: (0.5, 0.1, 0), INDEX_MCP: (0.5, 0.5, 0),
        MIDDLE_TIP: (0.5, 0.1, 0), MIDDLE_MCP: (0.5, 0.5, 0),
        RING_TIP: (0.5, 0.1, 0), RING_MCP: (0.5, 0.5, 0),
        PINKY_TIP: (0.2, 0.1, 0), PINKY_MCP: (0.2, 0.5, 0),
    })
    states = c._finger_states(lms)
    assert all(states.values())

def test_all_fingers_extended_left_hand():
    c = clf()
    # 왼손: THUMB_CMC가 PINKY_MCP보다 x가 작음 → thumb tip이 IP보다 x가 작아야 extended
    lms = make_lm({
        THUMB_CMC: (0.2, 0.5, 0), THUMB_TIP: (0.1, 0.5, 0), THUMB_IP: (0.3, 0.5, 0),
        INDEX_TIP: (0.5, 0.1, 0), INDEX_MCP: (0.5, 0.5, 0),
        MIDDLE_TIP: (0.5, 0.1, 0), MIDDLE_MCP: (0.5, 0.5, 0),
        RING_TIP: (0.5, 0.1, 0), RING_MCP: (0.5, 0.5, 0),
        PINKY_TIP: (0.8, 0.1, 0), PINKY_MCP: (0.8, 0.5, 0),
    })
    states = c._finger_states(lms)
    assert all(states.values())

def test_fist_all_curled():
    c = clf()
    lms = make_lm({
        THUMB_CMC: (0.8, 0.5, 0), THUMB_TIP: (0.6, 0.5, 0), THUMB_IP: (0.7, 0.5, 0),
        INDEX_TIP: (0.5, 0.75, 0), INDEX_MCP: (0.5, 0.5, 0),
        MIDDLE_TIP: (0.5, 0.75, 0), MIDDLE_MCP: (0.5, 0.5, 0),
        RING_TIP: (0.5, 0.75, 0), RING_MCP: (0.5, 0.5, 0),
        PINKY_TIP: (0.2, 0.75, 0), PINKY_MCP: (0.2, 0.5, 0),
    })
    states = c._finger_states(lms)
    assert not any(states.values())


def test_direction_right():
    assert clf()._direction(50.0, 0.0) == '→'

def test_direction_left():
    assert clf()._direction(-50.0, 0.0) == '←'

def test_direction_up():
    assert clf()._direction(0.0, -50.0) == '↑'

def test_direction_down():
    assert clf()._direction(0.0, 50.0) == '↓'

def test_direction_up_right():
    assert clf()._direction(40.0, -40.0) == '↗'

def test_direction_up_left():
    assert clf()._direction(-40.0, -40.0) == '↖'

def test_direction_down_right():
    assert clf()._direction(40.0, 40.0) == '↘'

def test_direction_down_left():
    assert clf()._direction(-40.0, 40.0) == '↙'

def test_direction_none_below_threshold():
    assert clf()._direction(5.0, 3.0) is None

def test_direction_none_zero():
    assert clf()._direction(0.0, 0.0) is None


def test_shake_triggers_on_two_reversals():
    c = clf()
    assert c._detect_shake(100) is False
    assert c._detect_shake(50) is False
    assert c._detect_shake(100) is False
    assert c._detect_shake(50) is True   # 2 reversals in window

def test_shake_not_triggered_on_one_reversal():
    c = clf()
    assert c._detect_shake(100) is False
    assert c._detect_shake(50) is False
    assert c._detect_shake(100) is False   # only 1 reversal — NOT 2

def test_tap_triggers_after_two_false_frames():
    # 포인팅 중 연속 2프레임 접힘 → 탭 인정
    c = clf()
    c._detect_tap(True)
    c._detect_tap(False)
    c._detect_tap(False)
    assert c._detect_tap(True) is True

def test_tap_not_triggered_on_single_frame_glitch():
    # 1프레임 노이즈는 탭이 아님
    c = clf()
    c._detect_tap(True)
    c._detect_tap(False)  # streak=1, 부족
    assert c._detect_tap(True) is False

def test_tap_not_triggered_on_fist_to_pointing():
    # 이전에 펼쳐 있지 않았으면 탭 아님
    c = clf()
    c._detect_tap(False)
    c._detect_tap(False)
    assert c._detect_tap(True) is False

def test_tap_not_triggered_when_always_pointing():
    c = clf()
    c._detect_tap(True)
    c._detect_tap(True)
    assert c._detect_tap(True) is False

def test_right_tap_triggers_after_two_false_frames():
    c = clf()
    c._detect_right_tap(True)
    c._detect_right_tap(False)
    c._detect_right_tap(False)
    assert c._detect_right_tap(True) is True

def test_right_tap_not_triggered_on_single_glitch():
    c = clf()
    c._detect_right_tap(True)
    c._detect_right_tap(False)
    assert c._detect_right_tap(True) is False


class MockHandLandmarks:
    def __init__(self, lms):
        self.landmark = lms

def test_classify_scroll_two_fingers_moving_down():
    c = clf()
    lms1 = make_lm({WRIST: (0.5, 0.5, 0), INDEX_TIP: (0.5, 0.1, 0), INDEX_MCP: (0.5, 0.4, 0),
                    MIDDLE_TIP: (0.5, 0.1, 0), MIDDLE_MCP: (0.5, 0.4, 0),
                    RING_TIP: (0.5, 0.7, 0), RING_MCP: (0.5, 0.5, 0),
                    PINKY_TIP: (0.3, 0.7, 0), PINKY_MCP: (0.3, 0.5, 0),
                    THUMB_CMC: (0.7, 0.5, 0), THUMB_TIP: (0.4, 0.5, 0), THUMB_IP: (0.5, 0.5, 0)})
    c.classify(MockHandLandmarks(lms1))
    lms2 = make_lm({WRIST: (0.5, 0.56, 0), INDEX_TIP: (0.5, 0.1, 0), INDEX_MCP: (0.5, 0.4, 0),
                    MIDDLE_TIP: (0.5, 0.1, 0), MIDDLE_MCP: (0.5, 0.4, 0),
                    RING_TIP: (0.5, 0.7, 0), RING_MCP: (0.5, 0.5, 0),
                    PINKY_TIP: (0.3, 0.7, 0), PINKY_MCP: (0.3, 0.5, 0),
                    THUMB_CMC: (0.7, 0.56, 0), THUMB_TIP: (0.4, 0.56, 0), THUMB_IP: (0.5, 0.56, 0)})
    result = c.classify(MockHandLandmarks(lms2))
    assert result is not None
    assert result.name == 'scroll'
    assert result.is_continuous is True
    assert result.dy > 0

def test_classify_pointer_move():
    c = clf()
    lms1 = make_lm({WRIST: (0.5, 0.8, 0),
                    INDEX_TIP: (0.5, 0.2, 0), INDEX_MCP: (0.5, 0.6, 0),
                    MIDDLE_TIP: (0.5, 0.85, 0), MIDDLE_MCP: (0.5, 0.7, 0),
                    RING_TIP: (0.5, 0.85, 0), RING_MCP: (0.5, 0.7, 0),
                    PINKY_TIP: (0.3, 0.85, 0), PINKY_MCP: (0.3, 0.7, 0),
                    THUMB_CMC: (0.7, 0.8, 0), THUMB_TIP: (0.4, 0.8, 0), THUMB_IP: (0.5, 0.8, 0)})
    c.classify(MockHandLandmarks(lms1))
    lms2 = make_lm({WRIST: (0.5, 0.8, 0),
                    INDEX_TIP: (0.53, 0.2, 0), INDEX_MCP: (0.5, 0.6, 0),
                    MIDDLE_TIP: (0.5, 0.85, 0), MIDDLE_MCP: (0.5, 0.7, 0),
                    RING_TIP: (0.5, 0.85, 0), RING_MCP: (0.5, 0.7, 0),
                    PINKY_TIP: (0.3, 0.85, 0), PINKY_MCP: (0.3, 0.7, 0),
                    THUMB_CMC: (0.7, 0.8, 0), THUMB_TIP: (0.4, 0.8, 0), THUMB_IP: (0.5, 0.8, 0)})
    result = c.classify(MockHandLandmarks(lms2))
    assert result is not None
    assert result.name == 'pointer_move'
    assert result.is_continuous is True
    assert result.x > 0.0

def test_classify_returns_none_for_no_landmark():
    c = clf()
    assert c.classify(None) is None
