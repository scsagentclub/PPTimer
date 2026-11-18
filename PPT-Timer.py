import tkinter as tk
from PIL import Image, ImageTk
import os
import sys
import json
import ctypes
import math
import time
from ctypes import wintypes
from tkinter import messagebox, simpledialog

user32 = ctypes.windll.user32

# ---------- Fullscreen detection (PPT / WPS / any slideshow) ----------

def any_fullscreen_excluding_self():
    """Return True if the foreground window covers the entire screen (PPT/WPS slideshow)."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    # Skip our own process
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == os.getpid():
        return False
    r = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return False
    w = r.right - r.left
    h = r.bottom - r.top
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    return w >= sw - 4 and h >= sh - 4


THEMES = {
    'dark': {
        'bg': '#0d0d0d', 'bar': '#0d0d0d', 'btn_bg': '#1a1a2e',
        'btn_fg': '#888888', 'timer_fg': '#e63946',
        'flash': '#e63946', 'menu_bg': '#1a1a2e', 'menu_active_bg': '#16213e'
    },
    'light': {
        'bg': '#f5f5f5', 'bar': '#f5f5f5', 'btn_bg': '#e0e0e0',
        'btn_fg': '#555555', 'timer_fg': '#d32f2f',
        'flash': '#d32f2f', 'menu_bg': '#ffffff', 'menu_active_bg': '#eeeeee'
    },
    'blue': {
        'bg': '#0a192f', 'bar': '#0a192f', 'btn_bg': '#112240',
        'btn_fg': '#8892b0', 'timer_fg': '#ff6b6b',
        'flash': '#ff6b6b', 'menu_bg': '#112240', 'menu_active_bg': '#233554'
    },
    'purple': {
        'bg': '#1a0b2e', 'bar': '#1a0b2e', 'btn_bg': '#2d1b4e',
        'btn_fg': '#a78bfa', 'timer_fg': '#f472b6',
        'flash': '#f472b6', 'menu_bg': '#2d1b4e', 'menu_active_bg': '#4c1d95'
    },
    'orange': {
        'bg': '#fff5e6', 'bar': '#fff5e6', 'btn_bg': '#ffcc80',
        'btn_fg': '#663300', 'timer_fg': '#c62828',
        'flash': '#c62828', 'menu_bg': '#fff5e6', 'menu_active_bg': '#ffcc80'
    },
    'mint': {
        'bg': '#e8f5e9', 'bar': '#e8f5e9', 'btn_bg': '#a5d6a7',
        'btn_fg': '#1b5e20', 'timer_fg': '#d32f2f',
        'flash': '#d32f2f', 'menu_bg': '#e8f5e9', 'menu_active_bg': '#a5d6a7'
    }
}


class CountdownTimer:
    def __init__(self):
        self.config = self.load_config()
        self.theme = self.config.get('theme', 'blue')
        self.auto_exit_slideshow = self.config.get('auto_exit_slideshow', True)

        self.root = tk.Tk()
        self.root.configure(bg=THEMES[self.theme]['bg'])
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)   # no title bar
        self.root.resizable(False, False)

        # Default 7 minutes
        self.duration_secs = 7 * 60
        self.remaining = self.duration_secs
        self.running = False
        self.after_id = None
        self.deadline = None
        self.flash_id = None
        self.editing_time = False
        self.ppt_was_active = True   # prevent trigger on first poll

        self.logo_path = self.find_logo()

        self.W = 170
        self.H = 40

        self.build_ui()
        self.update_display()

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        x = sw - self.W - 20
        self.root.geometry(f'{self.W}x{self.H}+{x}+20')

        # Keyboard
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<space>', lambda e: self.toggle())
        self.root.bind('<r>', lambda e: self.reset())
        self.root.bind('<s>', lambda e: self.set_time())
        self.root.bind('<plus>', lambda e: self.adjust(60))
        self.root.bind('<equal>', lambda e: self.adjust(60))
        self.root.bind('<minus>', lambda e: self.adjust(-60))

        # Mouse
        self.root.bind('<MouseWheel>', self.on_scroll)
        self.time_lbl.bind('<Button-3>', self.preset_menu)

        # Theme menu (will bind after logo/fallback created)
        self.theme_menu_btn = None

        # Drag window (no title bar)
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.do_drag)

        # Right-click empty area to exit (minimalist, no extra buttons)
        self.root.bind('<Button-3>', self.exit_menu)

        # PPT auto-detect polling — start after 2s delay
        self.root.after(2000, self.poll_ppt)

    # ---------- logo ----------

    def find_logo(self):
        if getattr(sys, 'frozen', False):
            # Only use bundled logo, never fallback to filesystem
            bundle = getattr(sys, '_MEIPASS', None)
            if bundle:
                for name in os.listdir(bundle):
                    low = name.lower()
                    if low.endswith('.png') and 'logo' in low:
                        return os.path.join(bundle, name)
        else:
            folder = os.path.dirname(os.path.abspath(__file__))
            for name in os.listdir(folder):
                low = name.lower()
                if low.endswith('.png') and 'logo' in low:
                    return os.path.join(folder, name)
        return None

    # ---------- window drag ----------

    def start_drag(self, event):
        self._dx = event.x_root - self.root.winfo_rootx()
        self._dy = event.y_root - self.root.winfo_rooty()

    def do_drag(self, event):
        x = event.x_root - self._dx
        y = event.y_root - self._dy
        self.root.geometry(f'+{x}+{y}')

    # ---------- theme ----------

    def config_path(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            folder = os.path.dirname(sys.executable)
        return os.path.join(folder, 'ppt_timer_config.json')

    def load_config(self):
        try:
            with open(self.config_path(), 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                cfg['theme'] = cfg.get('theme', 'blue')
                cfg['auto_exit_slideshow'] = cfg.get('auto_exit_slideshow', True)
                if cfg['theme'] not in THEMES:
                    cfg['theme'] = 'blue'
                return cfg
        except Exception:
            return {'theme': 'blue', 'auto_exit_slideshow': True}

    def save_config(self):
        try:
            with open(self.config_path(), 'w', encoding='utf-8') as f:
                json.dump({'theme': self.theme, 'auto_exit_slideshow': self.auto_exit_slideshow}, f)
        except Exception:
            pass

    def theme_color(self, key):
        return THEMES[self.theme].get(key, THEMES['blue'][key])

    def apply_theme(self, name):
        if name not in THEMES:
            return
        self.stop_flash()
        self.theme = name
        self.save_config()
        t = THEMES[name]
        self.root.configure(bg=t['bg'])
        self.bar.configure(bg=t['bar'])
        self.left.configure(bg=t['bar'])
        self.right.configure(bg=t['bar'])
        self.m_btn.configure(fg=t['btn_fg'], bg=t['btn_bg'])
        self.p_btn.configure(fg=t['btn_fg'], bg=t['btn_bg'])
        self.time_lbl.configure(fg=t['timer_fg'], bg=t['bg'])
        if self.logo_lbl is not None:
            self.logo_lbl.configure(bg=t['bar'])
        if self.theme_menu_btn:
            self.theme_menu_btn.configure(fg=t['btn_fg'], bg=t['btn_bg'])
        if self.fallback_lbl and self.fallback_lbl.winfo_exists():
            self.fallback_lbl.configure(fg=t['btn_fg'], bg=t['btn_bg'])
        self.update_display()

    def theme_menu(self, event):
        t = THEMES[self.theme]
        menu = tk.Menu(self.root, tearoff=0, bg=t['menu_bg'], fg=t.get('btn_fg', '#ffffff'),
                       activebackground=t['menu_active_bg'], activeforeground=t.get('btn_fg', '#ffffff'),
                       font=('Segoe UI', 10))
        labels = {'dark': '深色', 'light': '浅色', 'blue': '蓝色',
                  'purple': '紫色', 'orange': '暖橙', 'mint': '薄荷'}
        for name, label in labels.items():
            marker = '● ' if name == self.theme else '   '
            menu.add_command(label=marker + label, command=lambda n=name: self.apply_theme(n))
        menu.add_separator()
        menu.add_command(label='设定时间  S', command=self.set_time)
        menu.add_command(label='置顶/取消置顶', command=self.toggle_topmost)
        exit_marker = '开' if self.auto_exit_slideshow else '关'
        menu.add_command(label=f'倒计时结束退出全屏: {exit_marker}',
                         command=self.toggle_auto_exit_slideshow)
        menu.post(event.x_root, event.y_root)
        return 'break'

    # ---------- UI ----------

    def build_ui(self):
        t = THEMES[self.theme]
        self.bar = tk.Frame(self.root, bg=t['bar'], height=self.H)
        self.bar.pack(fill='both', expand=True, padx=2, pady=2)
        self.bar.pack_propagate(False)

        # -- Left: [-] time [+] --
        self.left = tk.Frame(self.bar, bg=t['bar'])
        self.left.pack(side='left', fill='y')

        # Minus
        self.m_btn = tk.Label(self.left, text='-', font=('Segoe UI', 11, 'bold'),
                              fg=t['btn_fg'], bg=t['btn_bg'], cursor='hand2')
        self.m_btn.pack(side='left', ipadx=3, ipady=0)
        self.m_btn.bind('<Button-1>', lambda e: self.adjust(-60))
        self.m_btn.bind('<Button-3>', lambda e: self.adjust(-300))

        # Time (click to start/pause)
        self.time_lbl = tk.Label(self.left, text='', font=('Segoe UI', 18, 'bold'),
                                 fg=t['timer_fg'], bg=t['bg'], cursor='hand2')
        self.time_lbl.pack(side='left', padx=3)
        self.time_lbl.bind('<Button-1>', lambda e: self.toggle())

        # Plus
        self.p_btn = tk.Label(self.left, text='+', font=('Segoe UI', 11, 'bold'),
                              fg=t['btn_fg'], bg=t['btn_bg'], cursor='hand2')
        self.p_btn.pack(side='left', ipadx=3, ipady=0)
        self.p_btn.bind('<Button-1>', lambda e: self.adjust(60))
        self.p_btn.bind('<Button-3>', lambda e: self.adjust(300))

        # -- Right: theme + logo (click to reset) --
        self.right = tk.Frame(self.bar, bg=t['bar'])
        self.right.pack(side='right', fill='y')

        self.theme_menu_btn = tk.Label(self.right, text='T', font=('Segoe UI', 8, 'bold'),
                                       fg=t['btn_fg'], bg=t['btn_bg'], cursor='hand2')
        self.theme_menu_btn.pack(side='right', ipadx=2, padx=(1, 0))
        self.theme_menu_btn.bind('<Button-1>', self.theme_menu)
        self.theme_menu_btn.bind('<Button-3>', self.exit_menu)

        self.fallback_lbl = None
        self.logo_lbl = None
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                img = Image.open(self.logo_path)
                img.thumbnail((60, 34), Image.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img)
                self.logo_lbl = tk.Label(self.right, image=self.logo_tk, bg=t['bar'], cursor='hand2')
                self.logo_lbl.pack(side='right')
                self.logo_lbl.bind('<Button-1>', lambda e: self.reset())
                self.logo_lbl.bind('<Button-3>', self.exit_menu)
            except Exception:
                self._fallback_label(self.right)
        else:
            self._fallback_label(self.right)

    def _fallback_label(self, parent):
        t = THEMES[self.theme]
        self.fallback_lbl = tk.Label(parent, text='R', font=('Segoe UI', 8, 'bold'),
                                     fg=t['btn_fg'], bg=t['btn_bg'], cursor='hand2')
        self.fallback_lbl.pack(side='right', ipadx=2, padx=(1, 0))
        self.fallback_lbl.bind('<Button-1>', lambda e: self.reset())
        self.fallback_lbl.bind('<Button-3>', self.exit_menu)

    # ---------- helpers ----------

    def fmt(self, secs):
        m, s = divmod(secs, 60)
        return f'{m:02d}:{s:02d}'

    def exit_menu(self, event):
        t = THEMES[self.theme]
        menu = tk.Menu(self.root, tearoff=0, bg=t['menu_bg'], fg=t.get('btn_fg', '#ffffff'),
                       activebackground=t['menu_active_bg'], activeforeground=t.get('btn_fg', '#ffffff'),
                       font=('Segoe UI', 10))
        exit_marker = '开' if self.auto_exit_slideshow else '关'
        menu.add_command(label=f'倒计时结束退出全屏: {exit_marker}',
                         command=self.toggle_auto_exit_slideshow)
        menu.add_command(label='设定时间  S', command=self.set_time)
        menu.add_command(label='置顶/取消置顶', command=self.toggle_topmost)
        menu.add_separator()
        menu.add_command(label='退出 Exit', command=self.root.destroy)
        menu.post(event.x_root, event.y_root)
        return 'break'

    def toggle_auto_exit_slideshow(self):
        self.auto_exit_slideshow = not self.auto_exit_slideshow
        self.save_config()

    def toggle_topmost(self):
        self.root.attributes('-topmost', not self.root.attributes('-topmost'))

    def update_display(self):
        t = THEMES[self.theme]
        self.time_lbl.config(text=self.fmt(self.remaining))
        self.time_lbl.config(fg=t['timer_fg'])

    # ---------- PPT auto-detect ----------

    def poll_ppt(self):
        is_active = any_fullscreen_excluding_self()
        if is_active and not self.ppt_was_active and not self.running and not self.editing_time:
            self.start()
        self.ppt_was_active = is_active
        self.root.after(1000, self.poll_ppt)

    # ---------- adjust ----------

    def adjust(self, delta):
        if self.running:
            return  # don't adjust while counting down
        new = self.remaining + delta
        if new < 1:
            new = 1
        if new > 99 * 60:
            new = 99 * 60
        self.remaining = new
        self.duration_secs = self.remaining
        self.update_display()

    def on_scroll(self, event):
        if self.running or event.delta == 0:
            return
        delta = 60 if event.delta > 0 else -60
        self.adjust(delta)

    def preset_menu(self, event):
        if self.running:
            return
        t = THEMES[self.theme]
        menu = tk.Menu(self.root, tearoff=0, bg=t['menu_bg'], fg=t.get('btn_fg', '#ffffff'),
                       activebackground=t['menu_active_bg'], activeforeground=t.get('btn_fg', '#ffffff'),
                       font=('Segoe UI', 11))
        for p in [1, 3, 5, 10, 15, 20, 25, 30, 45, 60]:
            s = p * 60
            menu.add_command(label=f'{p} 分钟', command=lambda secs=s: self.set_preset(secs))
        menu.add_separator()
        menu.add_command(label='自定义时间  S', command=self.set_time)
        menu.add_command(label='置顶/取消置顶', command=self.toggle_topmost)
        exit_marker = '开' if self.auto_exit_slideshow else '关'
        menu.add_command(label=f'倒计时结束退出全屏: {exit_marker}',
                         command=self.toggle_auto_exit_slideshow)
        menu.add_command(label='退出 Exit', command=self.root.destroy)
        menu.post(event.x_root, event.y_root)
        return 'break'

    def set_preset(self, secs):
        self.remaining = secs
        self.duration_secs = secs
        self.update_display()

    @staticmethod
    def parse_time(value):
        value = value.strip()
        if ':' in value:
            parts = value.split(':')
            if len(parts) != 2:
                raise ValueError('请使用 分:秒 格式')
            minutes, seconds = map(int, parts)
            if minutes < 0 or not 0 <= seconds < 60:
                raise ValueError('秒数必须在 0 到 59 之间')
            total = minutes * 60 + seconds
        else:
            minutes = float(value)
            if not math.isfinite(minutes):
                raise ValueError('请输入有限的分钟数')
            total = round(minutes * 60)
        if not 1 <= total <= 99 * 60 + 59:
            raise ValueError('时间必须在 1 秒到 99 分 59 秒之间')
        return total

    def set_time(self):
        was_running = self.running
        if was_running:
            self.pause()
        self.editing_time = True
        try:
            value = simpledialog.askstring('设定时间', '请输入分钟或 分:秒（例如 10 或 10:30）：',
                                           initialvalue=self.fmt(self.remaining), parent=self.root)
            if value is not None:
                try:
                    seconds = self.parse_time(value)
                except (ValueError, OverflowError) as error:
                    messagebox.showerror('输入错误', str(error), parent=self.root)
                else:
                    self.remaining = seconds
                    self.duration_secs = seconds
                    self.stop_flash()
                    self.update_display()
        finally:
            self.editing_time = False
            if was_running:
                self.start()

    # ---------- timer ----------

    def start(self):
        if self.running or self.editing_time:
            return
        if self.remaining <= 0:
            self.remaining = self.duration_secs
        self.stop_flash()
        self.deadline = time.monotonic() + self.remaining
        self.running = True
        self.tick()

    def pause(self):
        if not self.running:
            return
        self.remaining = max(0, math.ceil(self.deadline - time.monotonic()))
        self.running = False
        self.deadline = None
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.update_display()

    def toggle(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def exit_slideshow(self):
        """Send Escape key to exit PPT/WPS slideshow."""
        VK_ESCAPE = 0x1B
        user32.keybd_event(VK_ESCAPE, 0, 0, 0)
        user32.keybd_event(VK_ESCAPE, 0, 2, 0)  # KEYEVENTF_KEYUP

    def tick(self):
        if not self.running:
            return
        self.after_id = None
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            self.remaining = 0
            self.running = False
            self.deadline = None
            self.update_display()
            self.flash()
            fullscreen_active = any_fullscreen_excluding_self()
            # Do not restart for the same fullscreen session if Escape is ignored.
            self.ppt_was_active = fullscreen_active
            if self.auto_exit_slideshow and fullscreen_active:
                self.exit_slideshow()
            return
        self.remaining = math.ceil(remaining)
        self.update_display()
        until_next_second = remaining - (self.remaining - 1)
        self.after_id = self.root.after(max(1, math.ceil(until_next_second * 1000)), self.tick)

    def flash(self, count=0):
        t = THEMES[self.theme]
        if count >= 6:
            self.root.configure(bg=t['bg'])
            self.flash_id = None
            return
        self.root.configure(bg=t['flash'] if count % 2 == 0 else t['bg'])
        self.flash_id = self.root.after(300, lambda: self.flash(count + 1))

    def stop_flash(self):
        if self.flash_id is not None:
            self.root.after_cancel(self.flash_id)
            self.flash_id = None
        self.root.configure(bg=THEMES[self.theme]['bg'])

    def reset(self):
        self.running = False
        self.deadline = None
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.stop_flash()
        self.remaining = self.duration_secs
        self.update_display()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    CountdownTimer().run()
