#!/usr/bin/env python3
"""
C/C++ Compiler GUI
Supports drag-and-drop or file path input.
Requires: gcc/g++ installed on your system.
Optional for drag-and-drop: pip install tkinterdnd2
"""

import os
import sys
import subprocess
import threading
import shutil
import platform
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, font

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# ─────────────────────────── Compiler helpers ───────────────────────────

def detect_compiler(file_path: str) -> tuple[str, list[str]]:
    """Return (compiler_binary, base_flags) based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext in (".cpp", ".cxx", ".cc", ".c++"):
        compiler = "g++"
        flags = ["-std=c++17"]
    else:  
        compiler = "gcc"
        flags = ["-std=c11"]
    return compiler, flags


def find_compiler(compiler: str) -> str | None:
    """Return full path to compiler, or None if not found."""
    return shutil.which(compiler)


def build_command(
    source: str,
    output: str,
    extra_flags: list[str],
    optimization: str,
    warnings: bool,
) -> list[str]:
    compiler, base_flags = detect_compiler(source)
    exe = find_compiler(compiler)
    if exe is None:
        raise FileNotFoundError(
            f"Compiler '{compiler}' not found. "
            "Please install GCC/G++ (e.g. via MinGW on Windows, Xcode CLI on macOS, "
            "or your Linux package manager)."
        )
    cmd = [exe] + base_flags
    if warnings:
        cmd += ["-Wall", "-Wextra"]
    if optimization != "None":
        cmd.append(optimization)
    cmd += extra_flags
    cmd += [source, "-o", output]
    return cmd


def run_compilation(cmd: list[str]) -> tuple[int, str, str]:
    """Run compiler command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result.returncode, result.stdout, result.stderr


def run_executable(exe_path: str) -> tuple[int, str, str]:
    """Run the compiled binary, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [exe_path],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


# ─────────────────────────── GUI ────────────────────────────────────────

class CompilerApp:
    BG        = "#0e0e12"
    PANEL     = "#16161d"
    BORDER    = "#2a2a38"
    ACCENT    = "#00e5ff"
    ACCENT2   = "#7c3aed"
    SUCCESS   = "#22c55e"
    ERROR     = "#ef4444"
    WARNING   = "#f59e0b"
    FG        = "#e2e8f0"
    FG_DIM    = "#64748b"
    MONO      = ("Consolas", 10) if platform.system() == "Windows" else ("Menlo", 10)

    def __init__(self, root):
        self.root = root
        self.root.title("C / C++ Compiler")
        self.root.configure(bg=self.BG)
        self.root.minsize(820, 640)
        self.root.geometry("960x720")

        self._source_path = tk.StringVar()
        self._output_path = tk.StringVar()
        self._opt_level   = tk.StringVar(value="None")
        self._warnings    = tk.BooleanVar(value=True)
        self._run_after   = tk.BooleanVar(value=False)
        self._status      = tk.StringVar(value="Ready")
        self._extra_flags = tk.StringVar()

        self._build_ui()
        self._apply_styles()

        if DND_AVAILABLE:
            self._drop_label.drop_target_register(DND_FILES)
            self._drop_label.dnd_bind("<<Drop>>", self._on_drop)

    # ── UI construction ──────────────────────────────────────────────

    def _build_ui(self):
        root = self.root

        title_frame = tk.Frame(root, bg=self.BG, pady=14)
        title_frame.pack(fill=tk.X, padx=24)

        tk.Label(
            title_frame, text="⬡  C / C++ COMPILER",
            bg=self.BG, fg=self.ACCENT,
            font=("Courier New", 15, "bold"),
        ).pack(side=tk.LEFT)

        self._status_label = tk.Label(
            title_frame, textvariable=self._status,
            bg=self.BG, fg=self.FG_DIM,
            font=("Courier New", 9),
        )
        self._status_label.pack(side=tk.RIGHT, padx=4)

        sep = tk.Frame(root, bg=self.BORDER, height=1)
        sep.pack(fill=tk.X, padx=24)

        body = tk.Frame(root, bg=self.BG)
        body.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

        left  = tk.Frame(body, bg=self.BG, width=340)
        right = tk.Frame(body, bg=self.BG)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 16))
        left.pack_propagate(False)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        drop_outer = tk.Frame(left, bg=self.BORDER, bd=0)
        drop_outer.pack(fill=tk.X, pady=(0, 12))

        self._drop_label = tk.Label(
            drop_outer,
            text="⬇  Drop .c / .cpp file here\nor click Browse",
            bg=self.PANEL, fg=self.FG_DIM,
            font=("Courier New", 10),
            pady=28, cursor="hand2",
            relief=tk.FLAT, bd=0,
        )
        self._drop_label.pack(fill=tk.X, padx=1, pady=1)
        self._drop_label.bind("<Button-1>", lambda e: self._browse_source())
        self._drop_label.bind("<Enter>", lambda e: self._drop_label.config(fg=self.ACCENT))
        self._drop_label.bind("<Leave>", lambda e: self._drop_label.config(fg=self.FG_DIM))

        self._section(left, "SOURCE FILE")
        src_row = tk.Frame(left, bg=self.BG)
        src_row.pack(fill=tk.X, pady=(0, 12))
        self._entry(src_row, self._source_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn(src_row, "…", self._browse_source, small=True).pack(side=tk.LEFT, padx=(6, 0))

        self._section(left, "OUTPUT BINARY  (leave blank = auto)")
        out_row = tk.Frame(left, bg=self.BG)
        out_row.pack(fill=tk.X, pady=(0, 12))
        self._entry(out_row, self._output_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._btn(out_row, "…", self._browse_output, small=True).pack(side=tk.LEFT, padx=(6, 0))

        self._section(left, "OPTIONS")
        opts = tk.Frame(left, bg=self.BG)
        opts.pack(fill=tk.X, pady=(0, 12))

        tk.Label(opts, text="Optimisation", bg=self.BG, fg=self.FG_DIM,
                 font=("Courier New", 8)).grid(row=0, column=0, sticky=tk.W)
        opt_menu = ttk.Combobox(
            opts, textvariable=self._opt_level,
            values=["None", "-O1", "-O2", "-O3", "-Os", "-Og"],
            state="readonly", width=8,
        )
        opt_menu.grid(row=0, column=1, sticky=tk.W, padx=(8, 0))

        self._check(opts, "Enable -Wall -Wextra", self._warnings).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        self._check(opts, "Run after compile", self._run_after).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))

        self._section(left, "EXTRA FLAGS  (e.g. -lm -pthread)")
        self._entry(left, self._extra_flags).pack(fill=tk.X, pady=(0, 16))

        self._compile_btn = self._btn(
            left, "▶  COMPILE", self._start_compile,
            accent=True, pady=12,
        )
        self._compile_btn.pack(fill=tk.X, pady=(0, 6))
        self._run_btn = self._btn(left, "▷  RUN BINARY", self._start_run, pady=8)
        self._run_btn.pack(fill=tk.X)
        self._run_btn.config(state=tk.DISABLED)

        if not DND_AVAILABLE:
            tk.Label(
                left,
                text="ℹ  Install tkinterdnd2 for drag-and-drop",
                bg=self.BG, fg=self.FG_DIM, font=("Courier New", 7),
                wraplength=300,
            ).pack(pady=(10, 0))

        # ── Output console ──
        self._section(right, "COMPILER OUTPUT")
        self._output_box = scrolledtext.ScrolledText(
            right,
            bg="#0a0a0f", fg=self.FG,
            font=self.MONO,
            insertbackground=self.ACCENT,
            selectbackground=self.ACCENT2,
            relief=tk.FLAT, bd=0,
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self._output_box.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        self._output_box.tag_config("success", foreground=self.SUCCESS)
        self._output_box.tag_config("error",   foreground=self.ERROR)
        self._output_box.tag_config("warning", foreground=self.WARNING)
        self._output_box.tag_config("info",    foreground=self.ACCENT)
        self._output_box.tag_config("dim",     foreground=self.FG_DIM)
        self._output_box.tag_config("stdout",  foreground="#a3e635")

        self._btn(right, "✕  CLEAR", self._clear_output, small=True).pack(side=tk.RIGHT)

    # ── Widget helpers ──────────────────────────────────────────────

    def _section(self, parent, text):
        tk.Label(
            parent, text=text,
            bg=self.BG, fg=self.ACCENT,
            font=("Courier New", 7, "bold"),
        ).pack(anchor=tk.W, pady=(4, 2))

    def _entry(self, parent, var):
        e = tk.Entry(
            parent, textvariable=var,
            bg=self.PANEL, fg=self.FG,
            insertbackground=self.ACCENT,
            relief=tk.FLAT, bd=0,
            font=("Courier New", 9),
            highlightthickness=1,
            highlightbackground=self.BORDER,
            highlightcolor=self.ACCENT,
        )
        return e

    def _btn(self, parent, text, cmd, accent=False, small=False, pady=6):
        bg = self.ACCENT if accent else self.PANEL
        fg = self.BG     if accent else self.FG
        b = tk.Button(
            parent, text=text, command=cmd,
            bg=bg, fg=fg, activebackground=self.ACCENT2,
            activeforeground=self.FG,
            relief=tk.FLAT, bd=0,
            font=("Courier New", 8 if small else 9, "bold"),
            cursor="hand2",
            pady=pady, padx=10,
        )
        b.bind("<Enter>", lambda e, b=b: b.config(bg=self.ACCENT2, fg=self.FG))
        b.bind("<Leave>", lambda e, b=b, bg=bg, fg=fg: b.config(bg=bg, fg=fg))
        return b

    def _check(self, parent, text, var):
        return tk.Checkbutton(
            parent, text=text, variable=var,
            bg=self.BG, fg=self.FG_DIM,
            selectcolor=self.PANEL,
            activebackground=self.BG,
            font=("Courier New", 8),
        )

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TCombobox",
            fieldbackground=self.PANEL,
            background=self.PANEL,
            foreground=self.FG,
            selectbackground=self.ACCENT2,
            borderwidth=0,
        )

    # ── Event handlers ──────────────────────────────────────────────

    def _on_drop(self, event):
        """Handle drag-and-drop file."""
        raw = event.data.strip()
        if raw.startswith("{") and raw.endswith("}"):
            raw = raw[1:-1]
        self._set_source(raw)

    def _browse_source(self):
        path = filedialog.askopenfilename(
            title="Select C / C++ source file",
            filetypes=[
                ("C/C++ files", "*.c *.cpp *.cxx *.cc *.c++"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._set_source(path)

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Save compiled binary as",
            defaultextension="" if platform.system() != "Windows" else ".exe",
        )
        if path:
            self._output_path.set(path)

    def _set_source(self, path: str):
        self._source_path.set(path)
        p = Path(path)
        suffix = ".exe" if platform.system() == "Windows" else ""
        self._output_path.set(str(p.with_suffix(suffix)))
        self._drop_label.config(
            text=f"📄  {p.name}",
            fg=self.ACCENT,
        )
        self._status.set(f"Loaded: {p.name}")
        self._run_btn.config(state=tk.DISABLED)

    def _start_compile(self):
        src = self._source_path.get().strip()
        if not src:
            self._log("No source file selected.", "error")
            return
        if not os.path.isfile(src):
            self._log(f"File not found: {src}", "error")
            return

        out = self._output_path.get().strip()
        if not out:
            p = Path(src)
            suffix = ".exe" if platform.system() == "Windows" else ""
            out = str(p.with_suffix(suffix))
            self._output_path.set(out)

        extra = [f for f in self._extra_flags.get().split() if f]
        self._compile_btn.config(state=tk.DISABLED, text="⏳ Compiling…")
        self._status.set("Compiling…")
        self._clear_output()

        threading.Thread(
            target=self._compile_thread,
            args=(src, out, extra),
            daemon=True,
        ).start()

    def _compile_thread(self, src, out, extra):
        try:
            cmd = build_command(
                source=src,
                output=out,
                extra_flags=extra,
                optimization=self._opt_level.get(),
                warnings=self._warnings.get(),
            )
            self._log("$ " + " ".join(cmd), "dim")
            self._log("")
            returncode, stdout, stderr = run_compilation(cmd)
        except FileNotFoundError as e:
            self._log(str(e), "error")
            self._finish_compile(False, out)
            return
        except subprocess.TimeoutExpired:
            self._log("Compilation timed out.", "error")
            self._finish_compile(False, out)
            return

        if stdout:
            self._log(stdout, "info")
        if stderr:
            for line in stderr.splitlines():
                if "error:" in line.lower():
                    self._log(line, "error")
                elif "warning:" in line.lower():
                    self._log(line, "warning")
                else:
                    self._log(line, "dim")

        success = returncode == 0
        if success:
            self._log(f"\n✔  Compiled successfully  →  {out}", "success")
        else:
            self._log(f"\n✘  Compilation failed (exit {returncode})", "error")

        self._finish_compile(success, out)

        if success and self._run_after.get():
            self._run_binary(out)

    def _finish_compile(self, success, out):
        self.root.after(0, self._compile_btn.config,
                        {"state": tk.NORMAL, "text": "▶  COMPILE"})
        if success:
            self.root.after(0, self._run_btn.config, {"state": tk.NORMAL})
            self.root.after(0, self._status.set, "Compiled ✔")
        else:
            self.root.after(0, self._run_btn.config, {"state": tk.DISABLED})
            self.root.after(0, self._status.set, "Failed ✘")

    def _start_run(self):
        out = self._output_path.get().strip()
        if not out or not os.path.isfile(out):
            self._log("No compiled binary found. Please compile first.", "error")
            return
        self._run_btn.config(state=tk.DISABLED, text="⏳ Running…")
        self._status.set("Running…")
        threading.Thread(
            target=self._run_binary,
            args=(out,),
            daemon=True,
        ).start()

    def _run_binary(self, exe_path: str):
        self._log(f"\n─── Running: {exe_path} ───", "info")
        try:
            rc, stdout, stderr = run_executable(exe_path)
        except PermissionError:
            self._log("Permission denied. Try: chmod +x " + exe_path, "error")
            self.root.after(0, self._run_btn.config,
                            {"state": tk.NORMAL, "text": "▷  RUN BINARY"})
            return
        except subprocess.TimeoutExpired:
            self._log("Program timed out (30 s).", "error")
            self.root.after(0, self._run_btn.config,
                            {"state": tk.NORMAL, "text": "▷  RUN BINARY"})
            return

        if stdout:
            self._log(stdout, "stdout")
        if stderr:
            self._log(stderr, "warning")
        tag = "success" if rc == 0 else "error"
        self._log(f"\n─── Exited with code {rc} ───", tag)
        self.root.after(0, self._run_btn.config,
                        {"state": tk.NORMAL, "text": "▷  RUN BINARY"})
        self.root.after(0, self._status.set, f"Run done (code {rc})")

    # ── Output helpers ──────────────────────────────────────────────

    def _log(self, text: str, tag: str = ""):
        def _write():
            self._output_box.config(state=tk.NORMAL)
            if tag:
                self._output_box.insert(tk.END, text + "\n", tag)
            else:
                self._output_box.insert(tk.END, text + "\n")
            self._output_box.see(tk.END)
            self._output_box.config(state=tk.DISABLED)
        self.root.after(0, _write)

    def _clear_output(self):
        self._output_box.config(state=tk.NORMAL)
        self._output_box.delete("1.0", tk.END)
        self._output_box.config(state=tk.DISABLED)


# ─────────────────────────── Entry point ────────────────────────────────

def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = CompilerApp(root)

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        app._set_source(sys.argv[1])

    root.mainloop()


if __name__ == "__main__":
    main()