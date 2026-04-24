import os
import re
import tkinter as tk
from pathlib import Path
from datetime import datetime
import customtkinter as ctk
from ui.theme import ACCENT, CARD_BG, MUTED

# Log directory — UE5 stores logs in LocalAppData for packaged games
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", "")) / "R5" / "Saved" / "Logs"

# Line-level classification regex
_RE_LINE = re.compile(
    r"^\[[\d.:\-]+\]\[\s*\d+\]"   # timestamp + frame
    r"(?P<cat>[^:]+):"             # category name
    r"(?P<rest>.*)"                # rest of message
)

POLL_MS = 2500   # ms between live-tail refreshes


def _classify(line: str) -> str:
    """Return a tag name for a log line: 'error', 'warning', 'display', or 'default'."""
    m = _RE_LINE.match(line)
    if not m:
        return "default"
    cat  = m.group("cat").lower()
    rest = m.group("rest").lower()
    if "error" in cat or "crash" in cat or "fatal" in cat or rest.lstrip().startswith("error"):
        return "error"
    if "warning" in cat or rest.lstrip().startswith("warning"):
        return "warning"
    if "display" in cat or rest.lstrip().startswith("display"):
        return "display"
    return "default"


class LogsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._log_files: list[Path] = []
        self._selected_file: Path | None = None
        self._filter = "all"       # "all" | "warnings" | "errors"
        self._search = ""
        self._last_size = 0        # byte position for tail
        self._tail_job  = None     # after() handle
        self._all_lines: list[str] = []
        self._tailing = False
        self._visible_count = 0
        self._build()

    # ─────────────────────────────────────────────────────────────────
    # Layout
    # ─────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── page title ────────────────────────────────────────────────
        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        title_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            title_row, text="Game Logs",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        # ── toolbar ───────────────────────────────────────────────────
        tb = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        tb.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        tb.grid_columnconfigure(1, weight=1)

        # file selector
        self._file_var = ctk.StringVar(value="No logs found")
        self._file_menu = ctk.CTkOptionMenu(
            tb, variable=self._file_var, values=["No logs found"],
            width=240, height=30,
            fg_color="#0f172a", button_color=ACCENT, button_hover_color="#0f766e",
            command=self._on_file_select,
        )
        self._file_menu.grid(row=0, column=0, padx=(10, 8), pady=8)

        # level filter buttons
        fbar = ctk.CTkFrame(tb, fg_color="transparent")
        fbar.grid(row=0, column=1, sticky="w", padx=4)
        self._filter_btns = {}
        for label, key in [("All", "all"), ("Warn+", "warnings"), ("Errors", "errors")]:
            btn = ctk.CTkButton(
                fbar, text=label, width=64, height=28,
                fg_color=ACCENT if key == "all" else "#0f172a",
                hover_color="#0f766e",
                font=ctk.CTkFont(size=12),
                command=lambda k=key: self._set_filter(k),
            )
            btn.pack(side="left", padx=3)
            self._filter_btns[key] = btn

        # search
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        ctk.CTkEntry(
            tb, textvariable=self._search_var,
            placeholder_text="Search…", width=160, height=28,
        ).grid(row=0, column=2, padx=8)

        # right buttons
        rbf = ctk.CTkFrame(tb, fg_color="transparent")
        rbf.grid(row=0, column=3, padx=(0, 10), pady=8)
        ctk.CTkButton(rbf, text="Open Folder", width=100, height=28,
                      fg_color="#0f172a", hover_color="#334155",
                      command=self._open_folder).pack(side="left", padx=3)
        ctk.CTkButton(rbf, text="Refresh", width=72, height=28,
                      fg_color="#0f172a", hover_color="#334155",
                      command=self._load_selected).pack(side="left", padx=3)
        self._tail_btn = ctk.CTkButton(
            rbf, text="Live Tail: Off", width=100, height=28,
            fg_color="#0f172a", hover_color="#334155",
            command=self._toggle_tail,
        )
        self._tail_btn.pack(side="left", padx=3)

        # ── log display ───────────────────────────────────────────────
        self._textbox = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#0a0f1a", text_color="#94a3b8",
            corner_radius=8, wrap="none",
            state="disabled",
        )
        self._textbox.grid(row=2, column=0, sticky="nsew")

        # configure color tags on underlying tk.Text widget
        tw = self._textbox._textbox
        tw.tag_config("error",   foreground="#f87171")
        tw.tag_config("warning", foreground="#fbbf24")
        tw.tag_config("display", foreground="#67e8f9")
        tw.tag_config("default", foreground="#94a3b8")
        tw.tag_config("search",  background="#854d0e", foreground="white")

        # ── status bar ────────────────────────────────────────────────
        sb = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=6, height=26)
        sb.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        sb.grid_propagate(False)
        self._status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            sb, textvariable=self._status_var,
            font=ctk.CTkFont(size=10), text_color=MUTED,
        ).pack(side="left", padx=12, pady=4)

        self._live_lbl = ctk.CTkLabel(
            sb, text="",
            font=ctk.CTkFont(size=10), text_color=ACCENT,
        )
        self._live_lbl.pack(side="right", padx=12, pady=4)

        self.refresh()

    # ─────────────────────────────────────────────────────────────────
    # Public refresh (called when tab becomes active)
    # ─────────────────────────────────────────────────────────────────

    def refresh(self):
        self._stop_tail()
        self._tailing = False
        self._scan_files()
        if self._log_files:
            self._select_file(self._log_files[0])

    # ─────────────────────────────────────────────────────────────────
    # File management
    # ─────────────────────────────────────────────────────────────────

    def _scan_files(self):
        if not LOG_DIR.exists():
            self._log_files = []
            self._file_menu.configure(values=["Log folder not found"])
            self._file_var.set("Log folder not found")
            return

        files = sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        self._log_files = files

        labels = []
        for f in files:
            label = "Current Session" if f.name == "R5.log" else f.name
            labels.append(label)

        if labels:
            self._file_menu.configure(values=labels)
            self._file_var.set(labels[0])
        else:
            self._file_menu.configure(values=["No logs found"])
            self._file_var.set("No logs found")

    def _on_file_select(self, label: str):
        try:
            idx = list(self._file_menu.cget("values")).index(label)
        except ValueError:
            return
        if 0 <= idx < len(self._log_files):
            self._select_file(self._log_files[idx])

    def _select_file(self, path: Path):
        self._stop_tail()
        self._tailing = False
        self._selected_file = path
        self._last_size = 0
        self._all_lines = []
        self._load_selected()
        self._update_tail_btn()

    def _load_selected(self):
        if not self._selected_file or not self._selected_file.exists():
            self._set_status("File not found.")
            return
        try:
            text = self._selected_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self._set_status(f"Could not read file: {e}")
            return

        self._all_lines = text.splitlines()
        self._last_size = self._selected_file.stat().st_size
        self._apply_filter()

    # ─────────────────────────────────────────────────────────────────
    # Filtering and display
    # ─────────────────────────────────────────────────────────────────

    def _set_filter(self, key: str):
        self._filter = key
        for k, btn in self._filter_btns.items():
            btn.configure(fg_color=ACCENT if k == key else "#0f172a")
        self._apply_filter()

    def _apply_filter(self):
        search = self._search_var.get().lower()
        self._search = search
        level  = self._filter

        visible: list[tuple[str, str]] = []  # (line, tag)
        for line in self._all_lines:
            tag = _classify(line)
            if level == "errors"   and tag != "error":
                continue
            if level == "warnings" and tag not in ("error", "warning"):
                continue
            if search and search not in line.lower():
                continue
            visible.append((line, tag))

        self._render(visible, search)
        self._update_status()

    def _render(self, lines: list[tuple[str, str]], search: str):
        self._visible_count = len(lines)
        tw = self._textbox._textbox
        tw.configure(state="normal")
        tw.delete("1.0", "end")
        for line, tag in lines:
            tw.insert("end", line + "\n", tag)
        if search:
            start = "1.0"
            while True:
                pos = tw.search(search, start, nocase=True, stopindex="end")
                if not pos:
                    break
                end = f"{pos}+{len(search)}c"
                tw.tag_add("search", pos, end)
                start = end
        tw.configure(state="disabled")
        tw.see("end")

    def _tail_append(self, new_lines: list[str]):
        """Append only new matching lines without re-rendering the full buffer."""
        search = self._search
        level  = self._filter
        visible = []
        for line in new_lines:
            tag = _classify(line)
            if level == "errors"   and tag != "error":
                continue
            if level == "warnings" and tag not in ("error", "warning"):
                continue
            if search and search not in line.lower():
                continue
            visible.append((line, tag))

        self._visible_count += len(visible)

        if visible:
            tw = self._textbox._textbox
            tw.configure(state="normal")
            for line, tag in visible:
                tw.insert("end", line + "\n", tag)
            if search:
                # highlight only within the newly appended lines
                total_lines = int(tw.index("end-1c").split(".")[0])
                start = f"{total_lines - len(visible)}.0"
                while True:
                    pos = tw.search(search, start, nocase=True, stopindex="end")
                    if not pos:
                        break
                    end = f"{pos}+{len(search)}c"
                    tw.tag_add("search", pos, end)
                    start = end
            tw.configure(state="disabled")
            tw.see("end")

        self._update_status()

    # ─────────────────────────────────────────────────────────────────
    # Live tail
    # ─────────────────────────────────────────────────────────────────

    def _toggle_tail(self):
        if self._tailing:
            self._stop_tail()
            self._tailing = False
        else:
            self._tailing = True
            self._start_tail()
        self._update_tail_btn()

    def _update_tail_btn(self):
        if self._tailing:
            self._tail_btn.configure(text="Live Tail: On", fg_color=ACCENT, hover_color="#0f766e")
            self._live_lbl.configure(text="● Live")
        else:
            self._tail_btn.configure(text="Live Tail: Off", fg_color="#0f172a", hover_color="#334155")
            self._live_lbl.configure(text="")

    def _start_tail(self):
        self._tail_job = self.after(POLL_MS, self._tail_tick)

    def _stop_tail(self):
        if self._tail_job is not None:
            self.after_cancel(self._tail_job)
            self._tail_job = None

    def _tail_tick(self):
        if not self._tailing:
            return
        if not self._selected_file or not self._selected_file.exists():
            return
        try:
            new_size = self._selected_file.stat().st_size
            if new_size > self._last_size:
                with open(self._selected_file, "r", encoding="utf-8", errors="replace") as f:
                    f.seek(self._last_size)
                    new_text = f.read()
                self._last_size = new_size
                new_lines = new_text.splitlines()
                self._all_lines.extend(new_lines)
                self._tail_append(new_lines)
        except Exception:
            pass
        self._tail_job = self.after(POLL_MS, self._tail_tick)

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────

    def _update_status(self):
        mtime = (
            datetime.fromtimestamp(self._selected_file.stat().st_mtime).strftime("%H:%M:%S")
            if self._selected_file and self._selected_file.exists() else "—"
        )
        self._status_var.set(
            f"{len(self._all_lines):,} lines total  •  {self._visible_count:,} shown  •  {mtime}"
        )

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _open_folder(self):
        if LOG_DIR.exists():
            os.startfile(LOG_DIR)
