"""Countdown behavior tests without a desktop or real Windows key events."""
import ctypes
import importlib.util
import json
import heapq
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location('ppt_timer_app', Path(__file__).with_name('PPT-Timer.py'))
app = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'tkinter': Mock(), 'PIL': Mock()}), \
        patch.object(ctypes, 'windll', SimpleNamespace(user32=Mock()), create=True):
    spec.loader.exec_module(app)


class CountdownTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.config_path = Path(folder.name) / 'config.json'
        self.root = Mock()
        self.root.winfo_screenwidth.return_value = 1920
        patches = [
            patch.object(app.CountdownTimer, 'config_path', return_value=str(self.config_path)),
            patch.object(app.CountdownTimer, 'find_logo', return_value=None),
            patch.object(app.CountdownTimer, 'build_ui', lambda timer: setattr(timer, 'time_lbl', Mock())),
            patch.object(app.tk, 'Tk', return_value=self.root),
            patch.object(app.time, 'monotonic', return_value=100.0),
            patch.object(app, 'is_fullscreen_window', return_value=True),
            patch.object(app, 'fullscreen_foreground_window',
                         side_effect=lambda: 42 if self.fullscreen.return_value else None),
        ]
        mocks = [self.enterContext(p) for p in patches]
        self.clock, self.fullscreen, self.foreground = mocks[-3:]
        app.user32.reset_mock(return_value=True, side_effect=True)
        app.user32.GetForegroundWindow.return_value = 42
        self.timer = app.CountdownTimer()

    def finish(self):
        self.timer.start()
        self.clock.return_value = self.timer.deadline
        self.timer.tick()

    def fire_retries(self):
        """Invoke every scheduled exit-retry callback, including ones queued by retries."""
        fired = 0
        while True:
            calls = [c for c in self.root.after.call_args_list if c.args and c.args[0] == 600]
            if fired >= len(calls):
                return
            calls[fired].args[1]()
            fired += 1

    def test_default_countdown_exits_fullscreen_once_and_stays_at_zero(self):
        self.assertEqual(self.timer.remaining, 420)
        self.finish()
        self.timer.time_lbl.config.assert_any_call(text='00:00')
        self.assertFalse(self.timer.running)
        self.assertIsNone(self.timer.deadline)
        self.assertEqual(app.user32.keybd_event.call_count, 2)
        self.timer.poll_ppt()  # The same fullscreen window must not restart the timer.
        self.timer.tick()
        self.assertEqual(self.timer.remaining, 0)
        self.assertFalse(self.timer.running)
        self.assertEqual(app.user32.keybd_event.call_count, 2)

    def test_expiry_does_not_send_escape_to_a_non_fullscreen_window(self):
        self.fullscreen.return_value = False
        self.finish()
        self.assertEqual(self.timer.remaining, 0)
        app.user32.keybd_event.assert_not_called()

    def test_disabled_auto_exit_is_saved_and_respected_after_restart(self):
        self.timer.toggle_auto_exit_slideshow()
        self.timer = app.CountdownTimer()
        self.finish()
        self.assertEqual(self.timer.remaining, 0)
        app.user32.keybd_event.assert_not_called()

    def test_legacy_theme_only_config_enables_auto_exit(self):
        self.config_path.write_text(json.dumps({'theme': 'mint'}))
        self.timer = app.CountdownTimer()
        self.assertEqual(self.timer.theme, 'mint')
        self.finish()
        self.assertEqual(app.user32.keybd_event.call_count, 2)

    def test_invalid_config_uses_auto_exit_default(self):
        self.config_path.write_text('{invalid')
        self.timer = app.CountdownTimer()
        self.finish()
        self.assertEqual(app.user32.keybd_event.call_count, 2)

    def test_reset_and_restart_reuse_custom_duration_after_expiry(self):
        self.timer.set_preset(75)
        self.finish()
        self.assertEqual(self.timer.remaining, 0)
        self.timer.reset()
        self.assertEqual(self.timer.remaining, 75)
        self.assertFalse(self.timer.running)
        self.finish()
        self.timer.start()
        self.assertEqual(self.timer.remaining, 75)
        self.assertTrue(self.timer.running)

    def test_countdown_accounts_for_delayed_ticks_and_pause(self):
        self.timer.set_preset(75)
        self.timer.start()
        self.clock.return_value = 112.4
        self.timer.tick()
        self.assertEqual(self.timer.remaining, 63)
        self.timer.pause()
        self.clock.return_value = 200.0
        self.timer.start()
        self.assertEqual(self.timer.deadline, 263.0)

    def test_edit_while_running_updates_the_single_countdown(self):
        self.timer.start()
        with patch.object(app.simpledialog, 'askstring', return_value='1:15'):
            self.timer.set_time()
        self.assertEqual(self.timer.remaining, 75)
        self.assertTrue(self.timer.running)
        self.clock.return_value = self.timer.deadline
        self.timer.tick()
        self.assertEqual(self.timer.remaining, 0)
        self.timer.reset()
        self.assertEqual(self.timer.remaining, 75)

    def test_next_fullscreen_session_starts_same_duration(self):
        self.timer.set_preset(90)
        self.finish()
        self.fullscreen.return_value = False
        self.timer.poll_ppt()
        self.fullscreen.return_value = True
        self.timer.poll_ppt()
        self.assertEqual(self.timer.remaining, 90)
        self.assertTrue(self.timer.running)

    def test_theme_change_after_expiry_keeps_zero_without_a_logo(self):
        self.finish()
        for name in ('bar', 'left', 'right', 'm_btn', 'p_btn'):
            setattr(self.timer, name, Mock())
        self.timer.logo_lbl = None
        self.timer.fallback_lbl = None
        self.timer.apply_theme('mint')
        self.assertEqual(self.timer.remaining, 0)
        self.timer.time_lbl.config.assert_any_call(fg=app.THEMES['mint']['timer_fg'])

    def test_scheduled_callbacks_pass_last_second_and_finish(self):
        queue = []
        sequence = 0

        def schedule(delay, callback):
            nonlocal sequence
            sequence += 1
            heapq.heappush(queue, (self.clock.return_value + delay / 1000, sequence, callback))
            return sequence

        self.root.after.side_effect = schedule
        self.timer.set_preset(2)
        self.timer.start()
        while queue and queue[0][0] <= 102.2:
            instant, _, callback = heapq.heappop(queue)
            self.clock.return_value = instant
            callback()
        self.timer.time_lbl.config.assert_any_call(text='00:01')
        self.timer.time_lbl.config.assert_any_call(text='00:00')
        self.assertEqual(self.timer.remaining, 0)
        self.assertFalse(self.timer.running)
        self.assertEqual(app.user32.keybd_event.call_count, 2)

    def test_timer_focus_does_not_lose_presentation_target(self):
        self.timer.start()
        self.foreground.return_value = None
        self.foreground.side_effect = None
        app.user32.GetForegroundWindow.side_effect = [99, 42]
        self.clock.return_value = self.timer.deadline
        self.timer.tick()
        app.user32.SetForegroundWindow.assert_called_once_with(42)
        self.assertEqual(app.user32.keybd_event.call_count, 2)
        self.assertEqual(self.timer.remaining, 0)

    def test_denied_focus_targets_presentation_without_global_escape(self):
        app.user32.GetForegroundWindow.return_value = 99
        self.finish()
        app.user32.keybd_event.assert_not_called()
        app.user32.PostMessageW.assert_any_call(42, 0x0100, 0x1B, 0x00010001)
        app.user32.PostMessageW.assert_any_call(42, 0x0101, 0x1B, 0xC0010001)

    def test_closed_presentation_is_not_sent_escape(self):
        self.timer.start()
        self.fullscreen.return_value = False
        self.clock.return_value = self.timer.deadline
        self.timer.tick()
        self.assertEqual(self.timer.remaining, 0)
        app.user32.keybd_event.assert_not_called()
        app.user32.PostMessageW.assert_not_called()

    def test_expiry_targets_the_current_foreground_fullscreen_window(self):
        # Fullscreen video hands the show to a different window (media overlay).
        self.timer.start()
        self.foreground.side_effect = lambda: 99
        app.user32.GetForegroundWindow.return_value = 7  # focus stays elsewhere
        self.clock.return_value = self.timer.deadline
        self.timer.tick()
        app.user32.SetForegroundWindow.assert_called_once_with(99)
        app.user32.PostMessageW.assert_any_call(99, 0x0100, 0x1B, 0x00010001)
        app.user32.PostMessageW.assert_any_call(99, 0x0101, 0x1B, 0xC0010001)

    def test_exit_retries_while_slideshow_stays_fullscreen(self):
        self.finish()  # first Escape, consumed by stopping video/animation
        self.assertEqual(app.user32.keybd_event.call_count, 2)
        self.fire_retries()
        self.assertEqual(app.user32.keybd_event.call_count, 6)  # three attempts total

    def test_exit_retry_stops_once_slideshow_closes(self):
        self.finish()
        self.assertEqual(app.user32.keybd_event.call_count, 2)
        self.fullscreen.return_value = False
        self.fire_retries()
        self.assertEqual(app.user32.keybd_event.call_count, 2)

    def test_restart_cancels_pending_exit_retry(self):
        self.finish()
        self.assertIsNotNone(self.timer.exit_retry_id)
        self.timer.reset()
        self.assertIsNone(self.timer.exit_retry_id)
        self.fire_retries()
        self.assertEqual(app.user32.keybd_event.call_count, 2)


class FullscreenDetectionTests(unittest.TestCase):
    def setUp(self):
        self.api = self.enterContext(patch.object(app, 'user32', Mock()))
        self.api.IsWindow.return_value = True
        self.api.IsIconic.return_value = False
        self.api.MonitorFromWindow.return_value = 7
        self.window_rect = (1920, -200, 3200, 824)
        self.monitor_rect = (1920, -200, 3200, 824)

        def window_rect(hwnd, ptr):
            ptr._obj.left, ptr._obj.top, ptr._obj.right, ptr._obj.bottom = self.window_rect
            return True

        def monitor_info(monitor, ptr):
            rect = ptr._obj.rcMonitor
            rect.left, rect.top, rect.right, rect.bottom = self.monitor_rect
            return True

        self.api.GetWindowRect.side_effect = window_rect
        self.api.GetMonitorInfoW.side_effect = monitor_info

    def test_fullscreen_on_secondary_monitor_with_different_resolution(self):
        self.assertTrue(app.is_fullscreen_window(42))

    def test_window_not_covering_its_monitor_is_not_fullscreen(self):
        self.window_rect = (1920, -200, 3200, 784)
        self.assertFalse(app.is_fullscreen_window(42))

    def test_minimized_or_closed_window_is_not_fullscreen(self):
        self.api.IsIconic.return_value = True
        self.assertFalse(app.is_fullscreen_window(42))
        self.api.IsIconic.return_value = False
        self.api.IsWindow.return_value = False
        self.assertFalse(app.is_fullscreen_window(42))

    def test_desktop_is_not_a_presentation(self):
        def class_name(hwnd, buffer, length):
            buffer.value = 'WorkerW'
            return len(buffer.value)

        self.api.GetClassNameW.side_effect = class_name
        self.assertFalse(app.is_fullscreen_window(42))


if __name__ == '__main__':
    unittest.main()
