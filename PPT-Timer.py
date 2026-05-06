import tkinter as tk
from PIL import Image, ImageTk
import os
import sys
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

    # ---------- UI ----------

    def build_ui(self):
        bar = tk.Frame(self.root, bg='#0d0d0d', height=self.H)
        bar.pack(fill='both', expand=True, padx=4, pady=3)
        bar.pack_propagate(False)

        # -- Left: [-] time [+] --
        left = tk.Frame(bar, bg='#0d0d0d')
        left.pack(side='left', fill='y')

        # Minus
        m = tk.Label(left, text='-', font=('Segoe UI', 11, 'bold'),
                     fg='#888888', bg='#1a1a2e', cursor='hand2')
        m.pack(side='left', ipadx=3, ipady=0)
        m.bind('<Button-1>', lambda e: self.adjust(-60))
        m.bind('<Button-3>', lambda e: self.adjust(-300))

        # Time (click to start/pause)
        self.time_lbl = tk.Label(left, text='', font=('Segoe UI', 18, 'bold'),
                                 fg='#e63946', bg='#0d0d0d', cursor='hand2')
        self.time_lbl.pack(side='left', padx=3)
        self.time_lbl.bind('<Button-1>', lambda e: self.toggle())

        # Plus
        p = tk.Label(left, text='+', font=('Segoe UI', 11, 'bold'),
                     fg='#888888', bg='#1a1a2e', cursor='hand2')
        p.pack(side='left', ipadx=3, ipady=0)
        p.bind('<Button-1>', lambda e: self.adjust(60))
        p.bind('<Button-3>', lambda e: self.adjust(300))

        # -- Right: logo (click to reset) --
        right = tk.Frame(bar, bg='#0d0d0d')
        right.pack(side='right', fill='y')

        if self.logo_path and os.path.exists(self.logo_path):
            try:
                img = Image.open(self.logo_path)
                img.thumbnail((60, 34), Image.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(img)
                logo_lbl = tk.Label(right, image=self.logo_tk, bg='#0d0d0d', cursor='hand2')
                logo_lbl.pack(side='right')
                logo_lbl.bind('<Button-1>', lambda e: self.reset())
            except Exception:
                self._fallback_label(right)
        else:
            self._fallback_label(right)

    def _fallback_label(self, parent):
        lbl = tk.Label(parent, text='Reset', font=('Segoe UI', 9, 'bold'),
                       fg='#888888', bg='#0d0d0d', cursor='hand2')
        lbl.pack(side='right', padx=(0, 4))
        lbl.bind('<Button-1>', lambda e: self.reset())

    # ---------- helpers ----------

    def fmt(self, secs):
        m, s = divmod(secs, 60)
        return f'{m:02d}:{s:02d}'

    def update_display(self):
        self.time_lbl.config(text=self.fmt(self.remaining))
        if self.is_work:
            self.time_lbl.config(fg='#e63946')
        else:
            self.time_lbl.config(fg='#2ecc71')

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
        menu = tk.Menu(self.root, tearoff=0, bg='#1a1a2e', fg='#ffffff',
                       activebackground='#16213e', activeforeground='#ffffff',
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
        self.root.configure(bg='#e63946')
        self.root.after(300, lambda: self.root.configure(bg='#0d0d0d'))

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
