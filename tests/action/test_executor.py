from unittest.mock import patch
from gesture.classifier import Gesture
from action.executor import execute


def test_scroll_calls_trackpad_scroll():
    g = Gesture('scroll', is_continuous=True, dx=5.0, dy=20.0)
    with patch('action.executor.trackpad.scroll') as mock_scroll:
        execute(g)
        mock_scroll.assert_called_once_with(5.0, 20.0)


def test_mission_control_calls_system():
    g = Gesture('mission_control')
    with patch('action.executor.system_gestures.mission_control') as mock:
        execute(g)
        mock.assert_called_once()


def test_rect_left_half_calls_rectangle():
    g = Gesture('rect_left_half')
    with patch('action.executor.rectangle.left_half') as mock:
        execute(g)
        mock.assert_called_once()


def test_pointer_move_calls_pointer():
    g = Gesture('pointer_move', is_continuous=True, dx=3.0, dy=-2.0)
    with patch('action.executor.pointer.move') as mock:
        execute(g)
        mock.assert_called_once_with(3.0, -2.0)


def test_drag_start_calls_drag_start():
    g = Gesture('drag_start')
    with patch('action.executor.pointer.drag_start') as mock:
        execute(g)
        mock.assert_called_once()


def test_unknown_gesture_does_nothing():
    g = Gesture('unknown_gesture_xyz')
    execute(g)  # Should not raise
