#!/usr/bin/env python3
"""HandshakeProxy portable dashboard.

UI/orchestration layer for the existing project:
  dashboard -> Python controller -> compiled C++ engine
            -> protection-test gate -> GoLogin

The dashboard does not spoof fingerprints, falsify device identity, or
claim that a proxy is invisible. It also does not store proxy passwords
in config.json.

Expected layout:
Handshakeproxy-main/
  dashboard.py
  gologin.exe
  config.json
  python/main.py
  cpp/proxy_engine.exe       # compiled C++, not .cpp source
  logs/

Optional environment variables:
  HANDSHAKE_PYTHON
  HANDSHAKE_CPP
  HANDSHAKE_GOLOGIN
"""

from __future__ import annotations
import json
import os
import platform
import shutil
import subprocess
import sys
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

APP = "HANDSHAKE PROXY"
VERSION = "2.1.0"
GITHUB = "https://github.com/smigoh"

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
CONFIG = ROOT / "config.json"
LOG_DIR.mkdir(exist_ok=True)


class Dashboard(tk.Tk):
    BG = "#05090d"
    PANEL = "#091118"
    PANEL2 = "#0d1820"
    BORDER = "#1c303d"
    TEXT = "#eaf3f8"
    MUTED = "#8295a3"
    BLUE = "#1597ff"
    BLUE_DARK = "#075da5"
    GREEN = "#31e35a"
    RED = "#ff5545"
    AMBER = "#ffbd45"

    def __init__(self):
        super().__init__()
        self.title(f"{APP} • Portable Network Control")
        self.geometry("1420x900")
        self.minsize(1100, 720)
        self.configure(bg=self.BG)

        self.procs = {}
        self.connected = False
        self.protected = False

        self.provider = tk.StringVar(value="NodeMaven")
        self.protocol = tk.StringVar(value="SOCKS5")
        self.ip_mode = tk.StringVar(value="AUTO")
        self.host = tk.StringVar()
        self.port = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self.connection = tk.StringVar(value="● DISCONNECTED")
        self.items = {}

        self._style()
        self._build()
        self._load_config()
        self._log("Dashboard started")
        self.protocol("WM_DELETE_WINDOW", self.close)

    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(
            "HP.TCombobox",
            fieldbackground=self.PANEL2,
            background=self.PANEL2,
            foreground=self.TEXT,
            arrowcolor=self.TEXT,
            bordercolor=self.BORDER,
        )

    def _build(self):
        top = tk.Frame(self, bg="#071017", height=58)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="◈", bg="#071017", fg=self.BLUE,
                 font=("Segoe UI", 24, "bold")).pack(side="left", padx=(20, 8))
        tk.Label(top, text=APP, bg="#071017", fg=self.TEXT,
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(top, text="  /  PORTABLE NETWORK CONTROL",
                 bg="#071017", fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left")
        self.conn_label = tk.Label(top, textvariable=self.connection,
                                   bg="#071017", fg=self.RED,
                                   font=("Segoe UI", 9, "bold"))
        self.conn_label.pack(side="right", padx=20)

        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True)
        self._sidebar(body)

        self.content = tk.Frame(body, bg=self.BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._dashboard()

        footer = tk.Frame(self, bg="#071017", height=36)
        footer.pack(fill="x")
        footer.pack_propagate(False)
        tk.Label(footer, text="SMIGOH TECH", bg="#071017", fg=self.BLUE,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(18, 5))
        link = tk.Label(footer, text="github.com/smigoh", bg="#071017",
                        fg=self.TEXT, font=("Segoe UI", 9, "underline"),
                        cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda _: webbrowser.open(GITHUB))
        tk.Label(footer, text=f"HandshakeProxy {VERSION}", bg="#071017",
                 fg=self.MUTED, font=("Segoe UI", 9)).pack(side="right", padx=18)

    def _sidebar(self, parent):
        side = tk.Frame(parent, bg="#071017", width=210,
                        highlightthickness=1,
                        highlightbackground=self.BORDER)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Label(side, text="SMIGOH", bg="#071017", fg=self.TEXT,
                 font=("Segoe UI", 17, "bold")).pack(pady=(28, 0))
        tk.Label(side, text="TECH", bg="#071017", fg=self.BLUE,
                 font=("Segoe UI", 17, "bold")).pack()
        tk.Frame(side, bg=self.BLUE, height=2).pack(fill="x", padx=25, pady=18)

        buttons = [
            ("⌂", "Dashboard", self._dashboard),
            ("◎", "Proxy", self._proxy),
            ("✓", "Protection Test", self._protection_test),
            ("◉", "Browser", self._browser),
            ("▤", "Logs", self._logs),
            ("⚙", "Settings", self._settings),
            ("▣", "USB Organizer", self._usb),
            ("ⓘ", "About", self._about),
        ]
        for icon, text, cmd in buttons:
            tk.Button(
                side, text=f"  {icon}   {text}", command=cmd, anchor="w",
                bg="#071017", fg=self.TEXT, activebackground="#0c2840",
                activeforeground=self.TEXT, relief="flat",
                font=("Segoe UI", 10), cursor="hand2", padx=14, pady=10
            ).pack(fill="x", padx=8, pady=1)

        tk.Label(side, text="USB MODE", bg="#071017", fg=self.GREEN,
                 font=("Segoe UI", 9, "bold")).pack(side="bottom", pady=(0, 2))
        tk.Label(side, text=str(ROOT), bg="#071017", fg=self.MUTED,
                 font=("Segoe UI", 7), wraplength=180).pack(
                     side="bottom", padx=10, pady=(0, 15))

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _card(self, parent, title):
        f = tk.Frame(parent, bg=self.PANEL, highlightthickness=1,
                     highlightbackground=self.BORDER)
        tk.Label(f, text=title, bg=self.PANEL, fg=self.BLUE,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w",
                                                     padx=18, pady=(14, 10))
        return f

    def _dashboard(self):
        self._clear()
        root = tk.Frame(self.content, bg=self.BG)
        root.pack(fill="both", expand=True, padx=10, pady=10)
        for c, weight in enumerate((3, 2)):
            root.grid_columnconfigure(c, weight=weight)
        for r, weight in enumerate((1, 1, 0)):
            root.grid_rowconfigure(r, weight=weight)

        c = self._card(root, "CONNECTION")
        c.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        l = self._card(root, "LIVE STATUS / LOG")
        l.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        p = self._card(root, "PROTECTION STATUS")
        p.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        x = self._card(root, "COMPONENTS")
        x.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        q = self._card(root, "QUICK ACTIONS")
        q.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self._connection_card(c)
        self._log_card(l)
        self._protection_card(p)
        self._components(x)
        self._quick(q)

    def _field(self, parent, label, var, row, col, values=None, span=1,
               secret=False):
        parent.grid_columnconfigure(col, weight=1)
        box = tk.Frame(parent, bg=self.PANEL)
        box.grid(row=row, column=col, columnspan=span, sticky="ew",
                 padx=4, pady=4)
        tk.Label(box, text=label, bg=self.PANEL, fg=self.TEXT,
                 font=("Segoe UI", 8)).pack(anchor="w", pady=(0, 4))
        if values:
            w = ttk.Combobox(box, textvariable=var, values=values,
                             state="readonly", style="HP.TCombobox")
        else:
            w = tk.Entry(box, textvariable=var, show="●" if secret else "",
                         bg=self.PANEL2, fg=self.TEXT,
                         insertbackground=self.TEXT, relief="flat",
                         highlightthickness=1,
                         highlightbackground=self.BORDER)
        w.pack(fill="x", ipady=6)

    def _button(self, parent, text, cmd, primary=False):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=self.BLUE_DARK if primary else "#111c24",
            fg=self.TEXT, activebackground=self.BLUE,
            activeforeground="white", relief="flat", bd=0,
            highlightthickness=1, highlightbackground=self.BORDER,
            font=("Segoe UI", 9, "bold"), cursor="hand2", padx=15, pady=9
        )

    def _connection_card(self, parent):
        form = tk.Frame(parent, bg=self.PANEL)
        form.pack(fill="both", expand=True, padx=18, pady=5)
        self._field(form, "Provider", self.provider, 0, 0, ["NodeMaven"])
        self._field(form, "Protocol", self.protocol, 0, 1, ["SOCKS5"])
        self._field(form, "IP Mode", self.ip_mode, 0, 2,
                    ["AUTO", "IPv4", "IPv6", "DUAL"])
        self._field(form, "Proxy Host", self.host, 1, 0, span=2)
        self._field(form, "Port", self.port, 1, 2)
        self._field(form, "Username", self.username, 2, 0, span=2)
        self._field(form, "Password", self.password, 2, 2, secret=True)

        row = tk.Frame(parent, bg=self.PANEL)
        row.pack(fill="x", padx=18, pady=12)
        self._button(row, "CONNECT", self._connect, True).pack(
            side="left", padx=(0, 7))
        self._button(row, "DISCONNECT", self._disconnect).pack(
            side="left", padx=7)
        self._button(row, "OPEN NODEMAVEN", self._nodemaven).pack(
            side="right")
        tk.Label(parent, textvariable=self.status, bg=self.PANEL,
                 fg=self.MUTED, font=("Segoe UI", 9)).pack(
                     anchor="w", padx=18, pady=(0, 12))

    def _log_card(self, parent):
        self.log_text = tk.Text(parent, bg="#050a0e", fg="#c9d7df",
                                insertbackground=self.TEXT, relief="flat",
                                font=("Consolas", 9), wrap="none")
        self.log_text.pack(fill="both", expand=True, padx=12, pady=5)

    def _protection_card(self, parent):
        grid = tk.Frame(parent, bg=self.PANEL)
        grid.pack(fill="both", expand=True, padx=15, pady=5)
        for i, (label, key) in enumerate([
            ("Proxy", "proxy"), ("IPv4", "ipv4"), ("IPv6", "ipv6"),
            ("DNS", "dns"), ("WebRTC", "webrtc"), ("Fail-closed", "fallback")
        ]):
            r, c = divmod(i, 2)
            cell = tk.Frame(grid, bg=self.PANEL)
            cell.grid(row=r, column=c, sticky="ew", padx=5, pady=8)
            dot = tk.Label(cell, text="●", bg=self.PANEL, fg=self.MUTED,
                           font=("Segoe UI", 16))
            dot.pack(side="left", padx=(0, 8))
            value = tk.Label(cell, text="NOT TESTED", bg=self.PANEL,
                             fg=self.MUTED, font=("Segoe UI", 9, "bold"))
            value.pack(side="left")
            tk.Label(cell, text=label, bg=self.PANEL, fg=self.TEXT,
                     font=("Segoe UI", 9)).pack(side="left", padx=8)
            self.items[key] = (dot, value)

        self.banner = tk.Label(
            parent, text="●  PROTECTION NOT VERIFIED",
            bg="#15100a", fg=self.AMBER,
            font=("Segoe UI", 9, "bold"), pady=8)
        self.banner.pack(fill="x", padx=15, pady=8)

    def _components(self, parent):
        for name, path in [
            ("Python controller", self._python_path()),
            ("C++ executable", self._cpp_path()),
            ("GoLogin", self._gologin_path()),
        ]:
            row = tk.Frame(parent, bg=self.PANEL)
            row.pack(fill="x", padx=18, pady=7)
            tk.Label(row, text=name, width=18, anchor="w",
                     bg=self.PANEL, fg=self.TEXT,
                     font=("Segoe UI", 9, "bold")).pack(side="left")
            found = path is not None
            tk.Label(row, text="FOUND" if found else "NOT FOUND",
                     bg=self.PANEL, fg=self.GREEN if found else self.RED,
                     font=("Segoe UI", 9, "bold")).pack(side="left")
            tk.Label(row, text=str(path) if path else "No compatible file",
                     bg=self.PANEL, fg=self.MUTED,
                     font=("Consolas", 8)).pack(side="left", padx=10)

        tk.Label(
            parent,
            text="The C++ source file is not directly executable. Compile it "
                 "to an executable before the dashboard can launch it.",
            bg=self.PANEL, fg=self.MUTED, wraplength=470,
            justify="left", font=("Segoe UI", 8)
        ).pack(anchor="w", padx=18, pady=10)

    def _quick(self, parent):
        self._button(parent, "RUN PROTECTION TEST",
                     self._protection_test, True).pack(
                         side="left", padx=7, pady=10)
        self._button(parent, "START ALL", self._start_all, True).pack(
            side="left", padx=7, pady=10)
        self._button(parent, "STOP ALL", self._stop_all).pack(
            side="left", padx=7, pady=10)
        self._button(parent, "REFRESH", self._dashboard).pack(
            side="left", padx=7, pady=10)

    # ---------- discovery ----------

    def _resolve(self, env, candidates):
        override = os.getenv(env)
        if override:
            p = ROOT / override
            if p.is_file():
                return p
        for item in candidates:
            p = ROOT / item
            if p.is_file():
                return p
        return None

    def _python_path(self):
        return self._resolve("HANDSHAKE_PYTHON",
                             ["python/main.py", "main.py"])

    def _cpp_path(self):
        return self._resolve(
            "HANDSHAKE_CPP",
            ["cpp/proxy_engine.exe", "cpp/proxy_engine",
             "cpp/handshakeproxy.exe", "cpp/handshakeproxy"])

    def _gologin_path(self):
        return self._resolve(
            "HANDSHAKE_GOLOGIN",
            ["gologin.exe", "GoLogin.exe", "gologin"])

    # ---------- orchestration ----------

    def _start(self, name, command, cwd):
        old = self.procs.get(name)
        if old and old.poll() is None:
            self._log(f"{name}: already running")
            return True
        try:
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)                 if platform.system() == "Windows" else 0
            p = subprocess.Popen(
                command, cwd=str(cwd), stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags)
            self.procs[name] = p
            self._log(f"{name}: started (PID {p.pid})")
            return True
        except (OSError, ValueError) as exc:
            self._log(f"{name}: start failed: {exc}")
            messagebox.showerror(f"{name} startup failed", str(exc))
            return False

    def _connect(self):
        if not self.host.get().strip() or not self.port.get().strip():
            messagebox.showwarning(
                "Proxy settings", "Enter the SOCKS5 host and port first.")
            return

        self._log("CONNECT requested")
        py = self._python_path()
        if py:
            if not self._start("python", [sys.executable, str(py)],
                               py.parent):
                return
        else:
            self._log("Python controller not found")

        cpp = self._cpp_path()
        if cpp:
            if not self._start("cpp", [str(cpp)], cpp.parent):
                return
        else:
            self._log("Compiled C++ engine not found")

        self.connected = True
        self.connection.set("● CONNECTED")
        self.conn_label.configure(fg=self.GREEN)
        self._set_status("proxy", "STARTED", self.GREEN)
        self.status.set("Components started; protection test required")
        self._log("Component startup complete")

    def _disconnect(self):
        self._stop_all()
        self.connected = False
        self.protected = False
        self.connection.set("● DISCONNECTED")
        self.conn_label.configure(fg=self.RED)
        for key in self.items:
            self._set_status(key, "NOT TESTED", self.MUTED)
        self.banner.configure(text="●  PROTECTION NOT VERIFIED",
                              bg="#15100a", fg=self.AMBER)
        self.status.set("Disconnected")

    def _start_all(self):
        self._connect()
        self._log("START ALL: browser remains gated until real checks pass")

    def _stop_all(self):
        for name, p in list(self.procs.items()):
            if p.poll() is None:
                try:
                    p.terminate()
                    p.wait(timeout=3)
                except (OSError, subprocess.TimeoutExpired):
                    try:
                        p.kill()
                    except OSError:
                        pass
            self.procs.pop(name, None)
            self._log(f"{name}: stopped")
        self._log("Tracked components stopped")

    # ---------- protection / browser ----------

    def _protection_test(self):
        if not self.connected:
            messagebox.showwarning(
                "Protection Test", "Connect the components first.")
            return

        for key in self.items:
            self._set_status(key, "CHECK REQUIRED", self.AMBER)

        self._log("Protection test requested")
        messagebox.showinfo(
            "Protection Test",
            "The dashboard will not fabricate PASS results. Connect the "
            "project's real DNS/IPv4/IPv6/WebRTC/fail-closed test functions "
            "to this gate before marking the environment PROTECTED."
        )

    def _browser(self):
        if not self.protected:
            messagebox.showwarning(
                "GoLogin",
                "GoLogin is gated until the project's real protection "
                "checks verify the environment.")
            self._log("GoLogin blocked: protection not verified")
            return

        browser = self._gologin_path()
        if not browser:
            messagebox.showerror(
                "GoLogin", "gologin.exe was not found on the USB.")
            return

        self._start("gologin", [str(browser)], ROOT)

    # ---------- utility pages ----------

    def _proxy(self):
        messagebox.showinfo(
            "Proxy", "Use the Dashboard fields to configure SOCKS5.")

    def _logs(self):
        messagebox.showinfo(
            "Logs", str(LOG_DIR / "handshakeproxy.log"))

    def _settings(self):
        messagebox.showinfo(
            "Settings",
            "Portable paths are resolved from the application directory. "
            "Passwords are not written to config.json.")

    def _usb(self):
        try:
            u = shutil.disk_usage(ROOT)
            messagebox.showinfo(
                "USB Organizer",
                f"Root: {ROOT}\n\n"
                f"Used: {u.used / 2**30:.2f} GB\n"
                f"Free: {u.free / 2**30:.2f} GB\n"
                f"Total: {u.total / 2**30:.2f} GB")
        except OSError as exc:
            messagebox.showerror("USB Organizer", str(exc))

    def _about(self):
        messagebox.showinfo(
            "About",
            f"{APP} {VERSION}\n\n"
            "SMIGOH TECH\n"
            "https://github.com/smigoh")

    def _nodemaven(self):
        webbrowser.open("https://nodemaven.com/")
        self._log("NodeMaven website opened")

    # ---------- logging / config ----------

    def _load_config(self):
        if not CONFIG.is_file():
            self._log("config.json not found; using defaults")
            return
        try:
            d = json.loads(CONFIG.read_text(encoding="utf-8"))
            self.provider.set(str(d.get("provider", "NodeMaven")))
            self.protocol.set(str(d.get("protocol", "SOCKS5")))
            self.ip_mode.set(str(d.get("ip_mode", "AUTO")))
            self.host.set(str(d.get("host", "")))
            self.port.set(str(d.get("port", "")))
            self.username.set(str(d.get("username", "")))
            self._log("Safe configuration loaded; password was not loaded")
        except (OSError, json.JSONDecodeError) as exc:
            self._log(f"Config warning: {exc}")

    def _log(self, text):
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {text}\n"
        if hasattr(self, "log_text"):
            self.log_text.insert("end", line)
            self.log_text.see("end")
        try:
            with (LOG_DIR / "handshakeproxy.log").open(
                "a", encoding="utf-8") as f:
                f.write(line)
        except OSError:
            pass

    def _set_status(self, key, value, color):
        if key in self.items:
            dot, label = self.items[key]
            dot.configure(fg=color)
            label.configure(text=value, fg=color)

    def close(self):
        active = [n for n, p in self.procs.items() if p.poll() is None]
        if active and not messagebox.askyesno(
            "Exit", "Tracked components are running. Stop them and exit?"
        ):
            return
        self._stop_all()
        self.destroy()


if __name__ == "__main__":
    Dashboard().mainloop()
