import tkinter as tk
import time
import threading

# ── Sound ───────────────────────────────────────────────────────────

try:
    import winsound

    def play_sound():
        for _ in range(3):
            winsound.Beep(1000, 200)
            time.sleep(0.1)

except ImportError:
    def play_sound():
        print("\a")


def play_sound_async():
    threading.Thread(target=play_sound, daemon=True).start()


# ── Constants ───────────────────────────────────────────────────────

SESSIONS_BEFORE_LONG = 4

WORK_COLOR = "#e74c3c"
SHORT_BREAK_COLOR = "#2ecc71"
LONG_BREAK_COLOR = "#3498db"

BG_COLOR = "#1e1e2e"
SURFACE_COLOR = "#282840"
TEXT_COLOR = "#cdd6f4"
SUBTEXT_COLOR = "#6c7086"
BTN_HOVER = "#363654"
BTN_START_COLOR = "#a6e3a1"
BTN_PAUSE_COLOR = "#f9e2af"
BTN_RESET_COLOR = "#f38ba8"
RING_BG = "#45475a"


# ── Stepper ─────────────────────────────────────────────────────────

class Stepper(tk.Frame):
    """[−] 数值 [+] 三合一调节器，点击数字可键入自定义值"""

    def __init__(self, parent, label, value, min_val, max_val, step,
                 unit="分钟", on_change=None, color=TEXT_COLOR):
        super().__init__(parent, bg=BG_COLOR)
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.unit = unit
        self.on_change = on_change
        self.btn_color = color

        # 标题
        tk.Label(
            self, text=label, font=("Microsoft YaHei UI", 10, "bold"),
            bg=BG_COLOR, fg=SUBTEXT_COLOR,
        ).pack()

        row = tk.Frame(self, bg=BG_COLOR)
        row.pack(pady=(4, 0))

        # − 按钮
        self.minus_btn = tk.Canvas(
            row, width=32, height=30, bg=SURFACE_COLOR,
            highlightthickness=0, cursor="hand2",
        )
        self.minus_btn.create_text(16, 16, text="−", font=("Segoe UI", 15),
                                   fill=self.btn_color, tags="txt")
        self.minus_btn.pack(side="left")
        self.minus_btn.bind("<Button-1>", self._decrement)
        self._bind_hover(self.minus_btn)

        # 数值
        self.val_label = tk.Label(
            row, text=f"{value} {unit}", font=("Microsoft YaHei UI", 12, "bold"),
            bg=BG_COLOR, fg=TEXT_COLOR, width=6, cursor="hand2",
        )
        self.val_label.pack(side="left", padx=4)
        self.val_label.bind("<Button-1>", self._quick_edit)

        # + 按钮
        self.plus_btn = tk.Canvas(
            row, width=32, height=30, bg=SURFACE_COLOR,
            highlightthickness=0, cursor="hand2",
        )
        self.plus_btn.create_text(16, 16, text="+", font=("Segoe UI", 15),
                                  fill=self.btn_color, tags="txt")
        self.plus_btn.pack(side="left")
        self.plus_btn.bind("<Button-1>", self._increment)
        self._bind_hover(self.plus_btn)

    def _bind_hover(self, canvas):
        def on_enter(e):
            canvas.config(bg=BTN_HOVER)
        def on_leave(e):
            canvas.config(bg=SURFACE_COLOR)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)

    def _decrement(self, e=None):
        if self.value - self.step >= self.min_val:
            self.value -= self.step
            self._update()

    def _increment(self, e=None):
        if self.value + self.step <= self.max_val:
            self.value += self.step
            self._update()

    def _update(self):
        self.val_label.config(text=f"{self.value} {self.unit}")
        if self.on_change:
            self.on_change(self.value)

    def _quick_edit(self, e=None):
        """点击数字弹出输入框，支持直接键入"""
        dialog = tk.Toplevel(self.winfo_toplevel())
        dialog.title("设置时长")
        dialog.geometry("260x150")
        dialog.configure(bg=BG_COLOR)
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        parent = self.winfo_toplevel()
        x = parent.winfo_x() + (parent.winfo_width() - 260) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="输入时长", font=("Microsoft YaHei UI", 11),
                 bg=BG_COLOR, fg=TEXT_COLOR).pack(pady=(16, 10))

        entry_frame = tk.Frame(dialog, bg=BG_COLOR)
        entry_frame.pack()

        var = tk.StringVar(value=str(self.value))
        entry = tk.Entry(
            entry_frame, textvariable=var, width=5,
            font=("Microsoft YaHei UI", 20, "bold"), justify="center",
            bg=SURFACE_COLOR, fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat", bd=0,
        )
        entry.pack(ipady=4)
        entry.focus_set()
        entry.select_range(0, "end")

        tk.Label(entry_frame, text=self.unit, font=("Microsoft YaHei UI", 10),
                 bg=BG_COLOR, fg=SUBTEXT_COLOR).pack()

        def _apply(e=None):
            try:
                v = int(var.get())
                v = max(self.min_val, min(self.max_val, v))
            except ValueError:
                v = self.value
            self.value = v
            self._update()
            dialog.destroy()

        tk.Button(dialog, text="确定", font=("Microsoft YaHei UI", 10, "bold"),
                  bg=BTN_START_COLOR, fg=BG_COLOR, relief="flat",
                  padx=20, pady=4, cursor="hand2", command=_apply).pack(pady=8)
        entry.bind("<Return>", _apply)

    def set_value(self, v):
        self.value = v
        self.val_label.config(text=f"{v} {self.unit}")


# ── Main App ────────────────────────────────────────────────────────

class PomodoroApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("番茄时钟")
        self.root.geometry("540x640")
        self.root.resizable(True, True)
        self.root.minsize(340, 480)
        self.root.configure(bg=BG_COLOR)

        self._resize_after_id = None
        self._applied_canvas_size = 0
        self._steppers_narrow = None

        self.work_seconds = 25 * 60
        self.short_break_seconds = 5 * 60
        self.long_break_seconds = 15 * 60

        self.total_seconds = self.work_seconds
        self.remaining = self.total_seconds
        self.running = False
        self.mode = "work"
        self.completed_sessions = 0
        self.after_id = None

        self._build_ui()

        self.root.bind("<Configure>", self._on_root_configure)
        self.root.eval("tk::PlaceWindow . center")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._apply_resize)

    # ── UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.container = tk.Frame(self.root, bg=BG_COLOR)
        self.container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(1, weight=1)

        # 顶部：模式 + 轮次点
        header = tk.Frame(self.container, bg=BG_COLOR)
        header.grid(row=0, column=0, pady=(0, 6))

        self.mode_label = tk.Label(
            header, text="专注", font=("Microsoft YaHei UI", 14, "bold"),
            bg=BG_COLOR, fg=WORK_COLOR,
        )
        self.mode_label.pack()

        self.session_frame = tk.Frame(header, bg=BG_COLOR)
        self.session_frame.pack(pady=(8, 0))
        self._draw_session_dots()

        # 环形进度（中间区域随窗口伸缩）
        self.timer_host = tk.Frame(self.container, bg=BG_COLOR)
        self.timer_host.grid(row=1, column=0, sticky="nsew")
        self.timer_host.rowconfigure(0, weight=1)
        self.timer_host.columnconfigure(0, weight=1)

        self.canvas_size = 280
        self.canvas = tk.Canvas(
            self.timer_host, width=self.canvas_size, height=self.canvas_size,
            bg=BG_COLOR, highlightthickness=0,
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor="center",
                          width=self.canvas_size, height=self.canvas_size)
        self._draw_ring(1.0)

        self.timer_text = self.canvas.create_text(
            self.canvas_size // 2, self.canvas_size // 2 - 6,
            text=self._fmt(self.remaining),
            font=("Microsoft YaHei UI", 38, "bold"), fill=TEXT_COLOR,
        )
        self.sub_text = self.canvas.create_text(
            self.canvas_size // 2, self.canvas_size // 2 + 32,
            text="就绪",
            font=("Microsoft YaHei UI", 11), fill=SUBTEXT_COLOR,
        )

        # 按钮
        btn_frame = tk.Frame(self.container, bg=BG_COLOR)
        btn_frame.grid(row=2, column=0, pady=12)

        self.start_btn = tk.Button(
            btn_frame, text="开始", font=("Microsoft YaHei UI", 11, "bold"),
            width=8, bg=BTN_START_COLOR, fg=BG_COLOR,
            activebackground=BTN_START_COLOR, relief="flat", bd=0,
            padx=10, pady=6, cursor="hand2", command=self._toggle_timer,
        )
        self.start_btn.pack(side="left", padx=6)

        self.reset_btn = tk.Button(
            btn_frame, text="重置", font=("Microsoft YaHei UI", 11, "bold"),
            width=8, bg=BTN_RESET_COLOR, fg=BG_COLOR,
            activebackground=BTN_RESET_COLOR, relief="flat", bd=0,
            padx=10, pady=6, cursor="hand2", command=self._reset,
        )
        self.reset_btn.pack(side="left", padx=6)

        self.skip_btn = tk.Button(
            btn_frame, text="跳过", font=("Microsoft YaHei UI", 11, "bold"),
            width=8, bg=SURFACE_COLOR, fg=TEXT_COLOR,
            activebackground=SURFACE_COLOR, relief="flat", bd=0,
            padx=10, pady=6, cursor="hand2", command=self._skip,
        )
        self.skip_btn.pack(side="left", padx=6)

        # 时长调节器
        self.ctrl_frame = tk.Frame(self.container, bg=BG_COLOR)
        self.ctrl_frame.grid(row=3, column=0, pady=(8, 0), sticky="ew")
        self.ctrl_frame.columnconfigure(0, weight=1)
        self.ctrl_frame.columnconfigure(1, weight=1)
        self.ctrl_frame.columnconfigure(2, weight=1)

        self.work_stepper = Stepper(
            self.ctrl_frame, "工作时间", 25, 1, 120, 1,
            on_change=self._on_work_change, color=WORK_COLOR,
        )
        self.break_stepper = Stepper(
            self.ctrl_frame, "短休息", 5, 1, 60, 1,
            on_change=self._on_break_change, color=SHORT_BREAK_COLOR,
        )
        self.long_stepper = Stepper(
            self.ctrl_frame, "长休息", 15, 1, 120, 1,
            on_change=self._on_long_change, color=LONG_BREAK_COLOR,
        )
        self._steppers = (
            self.work_stepper, self.break_stepper, self.long_stepper,
        )

        # 底部提示（自动换行，避免被裁切）
        self.hint_label = tk.Label(
            self.container,
            text="点击 +/− 调节时间  ·  点击数字直接输入",
            font=("Microsoft YaHei UI", 8), bg=BG_COLOR, fg=SUBTEXT_COLOR,
            justify="center",
        )
        self.hint_label.grid(row=4, column=0, sticky="ew", pady=(12, 4))

        self.timer_host.bind("<Configure>", self._on_timer_host_configure)
        self._relayout_steppers(540)
        self.hint_label.config(wraplength=432)

    def _on_timer_host_configure(self, event):
        if event.widget is not self.timer_host:
            return
        self._schedule_resize()

    def _on_root_configure(self, event):
        if event.widget is not self.root:
            return
        self._schedule_resize()

    def _schedule_resize(self):
        if self._resize_after_id:
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(80, self._apply_resize)

    def _relayout_steppers(self, win_w):
        narrow = win_w < 460
        if narrow == self._steppers_narrow:
            return
        self._steppers_narrow = narrow
        for s in self._steppers:
            s.grid_forget()
        if narrow:
            for i, s in enumerate(self._steppers):
                s.grid(row=i, column=0, pady=6, sticky="ew")
        else:
            for i, s in enumerate(self._steppers):
                s.grid(row=0, column=i, padx=5, sticky="n")

    def _apply_resize(self):
        self._resize_after_id = None
        w, h = self.root.winfo_width(), self.root.winfo_height()
        if w < 100 or h < 100:
            return

        self.hint_label.config(wraplength=max(200, w - 48))
        self._relayout_steppers(w)

        self.timer_host.update_idletasks()
        host_w = self.timer_host.winfo_width()
        host_h = self.timer_host.winfo_height()
        if host_w < 40 or host_h < 40:
            return

        size = max(120, min(host_w - 16, host_h - 16, 520))
        if size == self._applied_canvas_size:
            return
        self._applied_canvas_size = size
        self.canvas_size = size
        self.canvas.place_configure(width=size, height=size)
        self._update_timer_layout()
        fraction = self.remaining / self.total_seconds if self.total_seconds else 0
        self._draw_ring(fraction)

    def _timer_font_size(self):
        return max(22, int(38 * self.canvas_size / 280))

    def _sub_font_size(self):
        return max(9, int(11 * self.canvas_size / 280))

    def _update_timer_layout(self):
        cx = cy = self.canvas_size // 2
        offset = max(4, int(6 * self.canvas_size / 280))
        sub_offset = max(24, int(32 * self.canvas_size / 280))
        self.canvas.coords(self.timer_text, cx, cy - offset)
        self.canvas.coords(self.sub_text, cx, cy + sub_offset)
        self.canvas.itemconfig(
            self.timer_text,
            font=("Microsoft YaHei UI", self._timer_font_size(), "bold"),
        )
        self.canvas.itemconfig(
            self.sub_text,
            font=("Microsoft YaHei UI", self._sub_font_size()),
        )

    def _draw_session_dots(self):
        for w in self.session_frame.winfo_children():
            w.destroy()
        for i in range(SESSIONS_BEFORE_LONG):
            color = WORK_COLOR if i < self.completed_sessions else RING_BG
            dot = tk.Canvas(
                self.session_frame, width=12, height=12,
                bg=BG_COLOR, highlightthickness=0,
            )
            dot.create_oval(1, 1, 11, 11, fill=color, outline="")
            dot.pack(side="left", padx=4)

    # ── Ring ────────────────────────────────────────────────────

    def _draw_ring(self, fraction):
        self.canvas.delete("ring")
        cx = cy = self.canvas_size // 2
        r = int(self.canvas_size * 110 / 280)
        w = max(6, int(self.canvas_size * 12 / 280))

        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=90, extent=-359.9, width=w,
            outline=RING_BG, style="arc", tags="ring",
        )

        color = {
            "work": WORK_COLOR,
            "short_break": SHORT_BREAK_COLOR,
            "long_break": LONG_BREAK_COLOR,
        }[self.mode]

        if fraction > 0:
            self.canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=90, extent=-360 * fraction, width=w,
                outline=color, style="arc", tags="ring",
            )

    # ── Timer ────────────────────────────────────────────────────

    def _toggle_timer(self):
        self._pause() if self.running else self._start()

    def _start(self):
        self.running = True
        self.start_btn.config(text="暂停", bg=BTN_PAUSE_COLOR,
                              activebackground=BTN_PAUSE_COLOR)
        self.canvas.itemconfig(self.sub_text, text="运行中…")
        self._tick()

    def _pause(self):
        self.running = False
        self.start_btn.config(text="开始", bg=BTN_START_COLOR,
                              activebackground=BTN_START_COLOR)
        self.canvas.itemconfig(self.sub_text, text="已暂停")
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _reset(self):
        was_running = self.running
        if was_running:
            self._pause()
        self.remaining = self.total_seconds
        if not was_running:
            self.canvas.itemconfig(self.sub_text, text="就绪")
        self._update_display()

    def _skip(self):
        self._pause()
        self.remaining = 0
        self._finish_session()

    def _tick(self):
        if not self.running:
            return
        self.remaining -= 1
        self._update_display()
        if self.remaining > 0:
            self.after_id = self.root.after(1000, self._tick)
        else:
            self.running = False
            self._finish_session()

    def _finish_session(self):
        play_sound_async()
        if self.mode == "work":
            self.completed_sessions += 1
            self._draw_session_dots()
            if self.completed_sessions >= SESSIONS_BEFORE_LONG:
                self.completed_sessions = 0
                self._draw_session_dots()
                self._switch_mode("long_break")
            else:
                self._switch_mode("short_break")
        else:
            self._switch_mode("work")

    def _switch_mode(self, mode):
        self.mode = mode
        if mode == "work":
            self.total_seconds = self.work_seconds
            self.mode_label.config(text="专注", fg=WORK_COLOR)
        elif mode == "short_break":
            self.total_seconds = self.short_break_seconds
            self.mode_label.config(text="休息", fg=SHORT_BREAK_COLOR)
        else:
            self.total_seconds = self.long_break_seconds
            self.mode_label.config(text="长休息", fg=LONG_BREAK_COLOR)

        self.remaining = self.total_seconds
        self.running = False
        self.start_btn.config(text="开始", bg=BTN_START_COLOR,
                              activebackground=BTN_START_COLOR)
        self.canvas.itemconfig(self.sub_text, text="就绪")
        self._update_display()

        try:
            self.root.attributes("-topmost", True)
            self.root.update()
            self.root.after(500, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass

    # ── Duration callbacks ───────────────────────────────────────

    def _on_work_change(self, v):
        self.work_seconds = v * 60
        if self.mode == "work":
            self.total_seconds = self.work_seconds
            self.remaining = min(self.remaining, self.total_seconds)
            if not self.running:
                self._reset()
            else:
                self._update_display()

    def _on_break_change(self, v):
        self.short_break_seconds = v * 60
        if self.mode == "short_break":
            self.total_seconds = self.short_break_seconds
            self.remaining = min(self.remaining, self.total_seconds)
            if not self.running:
                self._reset()
            else:
                self._update_display()

    def _on_long_change(self, v):
        self.long_break_seconds = v * 60
        if self.mode == "long_break":
            self.total_seconds = self.long_break_seconds
            self.remaining = min(self.remaining, self.total_seconds)
            if not self.running:
                self._reset()
            else:
                self._update_display()

    # ── Display ──────────────────────────────────────────────────

    def _update_display(self):
        fraction = self.remaining / self.total_seconds if self.total_seconds else 0
        self._draw_ring(fraction)
        self.canvas.itemconfig(self.timer_text, text=self._fmt(self.remaining))
        self._update_title()

    def _update_title(self):
        t = self._fmt(self.remaining)
        m = {"work": "专注", "short_break": "休息",
             "long_break": "长休息"}[self.mode]
        s = "▶" if self.running else "⏸"
        self.root.title(f"{t} - {m} {s}")

    @staticmethod
    def _fmt(seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _on_close(self):
        self.running = False
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PomodoroApp().run()
