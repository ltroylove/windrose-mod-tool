import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

from ui.app_window import AppWindow

if __name__ == "__main__":
    try:
        app = AppWindow()
        app.mainloop()
    except Exception:
        import traceback
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("BlackFlag Mod Manager — Error", traceback.format_exc())
        except Exception:
            print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)
