import tkinter as tk
from PIL import Image, ImageTk
import os
import sys
import json
import ctypes
from ctypes import wintypes

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
        'btn_fg': '#888888', 'work_fg': '#e63946', 'break_fg': '#2ecc71',
        'flash': '#e63946', 'menu_bg': '#1a1a2e', 'menu_active_bg': '#16213e'
    },
    'light': {
        'bg': '#f5f5f5', 'bar': '#f5f5f5', 'btn_bg': '#e0e0e0',
        'btn_fg': '#555555', 'work_fg': '#d32f2f', 'break_fg': '#388e3c',
        'flash': '#d32f2f', 'menu_bg': '#ffffff', 'menu_active_bg': '#eeeeee'
    },
    'blue': {
        'bg': '#0a192f', 'bar': '#0a192f', 'btn_bg': '#112240',
        'btn_fg': '#8892b0', 'work_fg': '#ff6b6b', 'break_fg': '#64ffda',
        'flash': '#ff6b6b', 'menu_bg': '#112240', 'menu_active_bg': '#233554'
    },
    'purple': {
        'bg': '#1a0b2e', 'bar': '#1a0b2e', 'btn_bg': '#2d1b4e',
        'btn_fg': '#a78bfa', 'work_fg': '#f472b6', 'break_fg': '#34d399',
        'flash': '#f472b6', 'menu_bg': '#2d1b4e', 'menu_active_bg': '#4c1d95'
    }
}


class PomodoroTimer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.configure(bg='#0d0d0d')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)   # no title bar
        self.root.resizable(False, False)

        # Default 10 minutes
        self.work_secs = 10 * 60
        self.break_secs = 5 * 60
        self.remaining = self.work_secs
        self.is_work = True
        self.running = False
        self.after_id = None
        self.ppt_was_active = True   # prevent trigger on first poll

        self.theme = self.load_theme()
        self.logo_path = self.find_logo()

        self.W = 190
        self.H = 44

        self.build_ui()
        self.update_display()

        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        x = sw - self.W - 20
        self.root.geometry(f'{self.W}x{self.H}+{x}+20')

        # Keyboard
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<space>', lambda e: self.toggle())

        # Mouse
        self.root.bind('<MouseWheel>', self.on_scroll)
        self.time_lbl.bind('<Button-3>', self.preset_menu)

        # Theme menu (will bind after logo/fallback created)
        self.theme_menu_btn = None

        # Drag window (no title bar)
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.do_drag)

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
        self._dx = event.x
        self._dy = event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + event.x - self._dx
        y = self.root.winfo_y() + event.y - self._dy
        self.root.geometry(f'+{x}+{y}')

    # ---------- theme ----------

    def config_path(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            folder = os.path.dirname(sys.executable)
        return os.path.join(folder, 'ppt_timer_config.json')

    def load_theme(self):
        try:
            with open(self.config_path(), 'r', encoding='utf-8') as f:
                name = json.load(f).get('theme', 'dark')
                return name if name in THEMES else 'dark'
        except Exception:
            return 'dark'

    def save_theme(self):
        try:
            with open(self.config_path(), 'w', encoding='utf-8') as f:
                json.dump({'theme': self.theme}, f)
        except Exception:
            pass

    def theme_color(self, key):
        return THEMES[self.theme].get(key, THEMES['dark'][key])

    def apply_theme(self, name):
        if name not in THEMES:
            return
        self.theme = name
        self.save_theme()
        t = THEMES[name]
        self.root.configure(bg=t['bg'])
        self.bar.configure(bg=t['bar'])
        self.left.configure(bg=t['bar'])
        self.right.configure(bg=t['bar'])
        self.m_btn.configure(fg=t['btn_fg'], bg=t['btn_bg'])
        self.p_btn.configure(fg=t['btn_fg'], bg=t['btn_bg'])
        if hasattr(self, 'logo_lbl'):
            self.logo_lbl.configure(bg=t['bar'])
        if self.theme_menu_btn:
            self.theme_menu_btn.configure(fg=t['btn_fg'], bg=t['btn_bg'])
        if self.fallback_lbl and self.fallback_lbl.winfo_exists():
            self.fallback_lbl.configure(fg=t['btn_fg'], bg=t['bar'])
        self.update_display()

    def theme_menu(self, event):
        t = THEMES[self.theme]
        menu = tk.Menu(self.root, tearoff=0, bg=t['menu_bg'], fg=t.get('btn_fg', '#ffffff'),
                       activebackground=t['menu_active_bg'], activeforeground=t.get('btn_fg', '#ffffff'),
                       font=('Segoe UI', 10))
        labels = {'dark': '深色', 'light': '浅色', 'blue': '蓝色', 'purple': '紫色'}
        for name, label in labels.items():
            marker = '● ' if name == self.theme else '   '
            menu.add_command(label=marker + label, command=lambda n=name: self.apply_theme(n))
        menu.post(event.x_root, event.y_root)

    # ---------- UI ----------

    def build_ui(self):
        t = THEMES[self.theme]
        self.bar = tk.Frame(self.root, bg=t['bar'], height=self.H)
        self.bar.pack(fill='both', expand=True, padx=4, pady=3)
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
                                 fg=t['work_fg'], bg=t['bg'], cursor='hand2')
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
        self.theme_menu_btn.pack(side='right', ipadx=3, padx=(2, 0))
        self.theme_menu_btn.bind('<Button-1>', self.theme_menu)

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
            except Exception:
                self._fallback_label(self.right)
        else:
            self._fallback_label(self.right)

    def _fallback_label(self, parent):
        t = THEMES[self.theme]
        self.fallback_lbl = tk.Label(parent, text='Reset', font=('Segoe UI', 9, 'bold'),
                                     fg=t['btn_fg'], bg=t['bar'], cursor='hand2')
        self.fallback_lbl.pack(side='right', padx=(0, 4))
        self.fallback_lbl.bind('<Button-1>', lambda e: self.reset())

    # ---------- helpers ----------

    def fmt(self, secs):
        m, s = divmod(secs, 60)
        return f'{m:02d}:{s:02d}'

    def update_display(self):
        t = THEMES[self.theme]
        self.time_lbl.config(text=self.fmt(self.remaining))
        self.time_lbl.config(fg=t['work_fg'] if self.is_work else t['break_fg'])

    # ---------- PPT auto-detect ----------

    def poll_ppt(self):
        is_active = any_fullscreen_excluding_self()
        if is_active and not self.ppt_was_active and not self.running:
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
        if self.is_work:
            self.work_secs = self.remaining
        else:
            self.break_secs = self.remaining
        self.update_display()

    def on_scroll(self, event):
        if self.running:
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
        menu.post(event.x_root, event.y_root)

    def set_preset(self, secs):
        self.remaining = secs
        if self.is_work:
            self.work_secs = secs
        else:
            self.break_secs = secs
        self.update_display()

    # ---------- timer ----------

    def start(self):
        self.running = True
        self.tick()

    def toggle(self):
        if self.running:
            self.running = False
            if self.after_id:
                self.root.after_cancel(self.after_id)
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
        if self.remaining <= 0:
            self.running = False
            self.flash()
            self.exit_slideshow()
            self.switch_mode()
            return
        self.remaining -= 1
        self.update_display()
        self.after_id = self.root.after(1000, self.tick)

    def flash(self):
        t = THEMES[self.theme]
        self.root.configure(bg=t['flash'])
        self.root.after(300, lambda: self.root.configure(bg=t['bg']))

    def reset(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
        secs = self.work_secs if self.is_work else self.break_secs
        self.remaining = (secs // 60) * 60  # ensure whole minute
        self.update_display()

    def switch_mode(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.is_work = not self.is_work
        self.remaining = self.work_secs if self.is_work else self.break_secs
        self.update_display()

    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    PomodoroTimer().run()
