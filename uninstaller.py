#!/usr/bin/env python3
"""
OpenBlox Uninstaller
Removes OpenBlox installation and optionally all user data.
"""

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk


REPO_URL = "https://github.com/Artemcik5/OpenBlox.git"


def _appdata_root() -> str:
    base = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA") or os.path.dirname(__file__)
    return os.path.join(base, "OpenBlox")


def get_local_version(install_dir: str) -> str:
    version_path = os.path.join(install_dir, "version")
    if os.path.isfile(version_path):
        with open(version_path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    return "-"


class UninstallerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("OpenBlox Uninstaller")
        root.geometry("520x360")
        root.minsize(480, 320)
        root.configure(bg="#0f1622")
        self.install_dir = tk.StringVar()
        self.remove_data = tk.BooleanVar(value=False)
        self.confirm = tk.BooleanVar(value=False)
        self._style()
        self._build_ui()
        self._detect_existing()

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#0f1622", foreground="#e2e8f0",
                        troughcolor="#0d1117", selectbackground="#1f6feb",
                        font=("Segoe UI", 10), borderwidth=0)
        style.configure("TFrame", background="#0f1622")
        style.configure("TLabel", background="#0f1622", foreground="#e2e8f0")
        style.configure("Red.TButton", background="#da3633", foreground="#ffffff",
                        borderwidth=0, padding=(12, 5))
        style.map("Red.TButton", background=[("active", "#f85149"), ("disabled", "#3a1a18")])
        style.configure("TCheckbutton", background="#0f1622", foreground="#e2e8f0")
        style.map("TCheckbutton", foreground=[("disabled", "#484f58")])
        style.configure("TEntry", fieldbackground="#0d1117", foreground="#e2e8f0",
                        bordercolor="#30363d", borderwidth=1, padding=4)
        style.configure("Horizontal.TProgressbar", background="#f85149", troughcolor="#0d1117")

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main, text="OpenBlox Uninstaller",
                 font=("Segoe UI", 15, "bold"), foreground="#f85149").pack(anchor=tk.W)
        ttk.Label(main, text="Remove OpenBlox from your system",
                 font=("Segoe UI", 9), foreground="#8b949e").pack(anchor=tk.W, pady=(0, 12))

        pf = ttk.Frame(main)
        pf.pack(fill=tk.X, pady=4)
        ttk.Label(pf, text="Install path:").pack(anchor=tk.W)
        row = ttk.Frame(pf)
        row.pack(fill=tk.X, pady=3)
        self.path_entry = ttk.Entry(row, textvariable=self.install_dir, state="readonly")
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.info_frame = ttk.LabelFrame(main, text="Status", padding=8)
        self.info_frame.pack(fill=tk.X, pady=10)
        self.local_label = ttk.Label(self.info_frame, text="Installed: -", font=("Segoe UI", 9))
        self.local_label.pack(anchor=tk.W)
        data_path = _appdata_root()
        self.data_label = ttk.Label(self.info_frame, text=f"User data: {data_path}",
                                    font=("Segoe UI", 9), foreground="#8b949e")
        self.data_label.pack(anchor=tk.W)

        self.confirm_cb = ttk.Checkbutton(main, text="I understand this will uninstall OpenBlox",
                                          variable=self.confirm, command=self._update_btn)
        self.confirm_cb.pack(anchor=tk.W, pady=(8, 2))
        self.data_cb = ttk.Checkbutton(main, text="Remove all data (chats, config, settings)",
                                       variable=self.remove_data)
        self.data_cb.pack(anchor=tk.W, pady=(0, 6))

        self.progress = ttk.Progressbar(main, mode="indeterminate", length=400)
        self.progress.pack(fill=tk.X, pady=(6, 0))
        self.log_text = tk.Text(main, height=4, wrap=tk.WORD, bg="#0d1117", fg="#8b949e",
                                font=("Consolas", 9), borderwidth=0, highlightthickness=1,
                                highlightbackground="#30363d", state=tk.DISABLED)
        self.log_text.pack(fill=tk.X, pady=(6, 0))
        btn_row = ttk.Frame(main)
        btn_row.pack(fill=tk.X, pady=(10, 0))
        self.uninstall_btn = ttk.Button(btn_row, text="Uninstall", style="Red.TButton",
                                        command=self._start_uninstall, state=tk.DISABLED)
        self.uninstall_btn.pack(side=tk.RIGHT)
        self._log("Confirm above and click Uninstall.")

    def _log(self, msg: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _update_btn(self):
        self.uninstall_btn.config(state=tk.NORMAL if self.confirm.get() else tk.DISABLED)

    def _detect_existing(self):
        path = os.path.dirname(os.path.abspath(__file__))
        self.install_dir.set(path)
        if not os.path.isdir(path):
            self.local_label.config(text="Installed: not found")
            return
        local = get_local_version(path)
        self.local_label.config(
            text=f"Installed: v{local}" if local != "-" else "Installed: (unknown version)")

    def _start_uninstall(self):
        self.confirm_cb.config(state=tk.DISABLED)
        self.data_cb.config(state=tk.DISABLED)
        self.uninstall_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)
        threading.Thread(target=self._uninstall_thread, daemon=True).start()

    def _uninstall_thread(self):
        path = self.install_dir.get()
        errors = []

        self.root.after(0, self._log, "Removing installation files...")
        skip_names = {"config.json", "chats", "uploads", "uninstaller.py", "__pycache__"}
        for item in os.listdir(path):
            if item in skip_names:
                continue
            item_path = os.path.join(path, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                else:
                    shutil.rmtree(item_path)
                self.root.after(0, self._log, f"  Removed {item}")
            except Exception as e:
                errors.append(f"{item}: {e}")

        if self.remove_data.get():
            data_dir = _appdata_root()
            if os.path.isdir(data_dir):
                self.root.after(0, self._log, "Removing user data...")
                try:
                    shutil.rmtree(data_dir)
                    self.root.after(0, self._log, f"  Removed {data_dir}")
                except Exception as e:
                    errors.append(f"User data: {e}")
            else:
                self.root.after(0, self._log, "No user data found to remove.")

        if errors:
            ok = False
            for e in errors:
                self.root.after(0, self._log, f"ERROR: {e}")

        self.root.after(0, self._uninstall_done, ok)

    def _uninstall_done(self, ok: bool):
        self.progress.stop()
        if ok:
            self._log("Uninstall complete. Cleaning up remaining files...")
            self._schedule_cleanup()
        else:
            self._log("Uninstall finished with errors.")
            messagebox.showerror("Uncomplete",
                "Some files could not be removed.\n"
                "Close any running OpenBlox processes and try again.")
            self.root.after(1000, self.root.destroy)

    def _schedule_cleanup(self):
        path = self.install_dir.get()
        data_dir = _appdata_root()
        bat_path = os.path.join(os.environ.get("TEMP", path), "openblox_cleanup.bat")
        lines = [
            "@echo off",
            "timeout /t 2 /nobreak >nul",
        ]
        if os.path.isdir(path):
            lines.append(f'rmdir /s /q "{path}" 2>nul')
        if self.remove_data.get() and os.path.isdir(data_dir):
            lines.append(f'rmdir /s /q "{data_dir}" 2>nul')
        lines.append(f'del "{bat_path}" 2>nul')
        try:
            with open(bat_path, "w") as f:
                f.write("\n".join(lines) + "\n")
            subprocess.Popen(["cmd", "/c", bat_path], close_fds=True,
                             creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Uninstall Complete",
                "OpenBlox has been removed.\n\n"
                "The install directory will be deleted shortly.")
        except Exception as e:
            messagebox.showinfo("Uninstall Complete",
                "OpenBlox has been removed.\n\n"
                f"Manual cleanup may be needed: {e}")
        self.root.after(500, self.root.destroy)


def main():
    root = tk.Tk()
    UninstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
