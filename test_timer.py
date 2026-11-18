"""Countdown behavior tests without a desktop or real Windows key events."""
import ctypes
import importlib.util
import json
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
            patch.object(app, 'any_fullscreen_excluding_self', return_value=True),
        ]
        mocks = [self.enterContext(p) for p in patches]
        self.clock, self.fullscreen = mocks[-2:]
        app.user32.reset_mock()
        self.timer = app.CountdownTimer()

    def finish(self):
        self.timer.start()
        self.clock.return_value = self.timer.deadline
        self.timer.tick()

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


if __name__ == '__main__':
    unittest.main()
