# ⬡ C / C++ Compiler GUI

A dark-themed desktop GUI for compiling and running C and C++ source files, built with Python and Tkinter. Supports drag-and-drop file loading, configurable compiler flags, and an integrated output console.

---

## Features

- **Auto-detects compiler** — uses `gcc` for `.c` files and `g++` for `.cpp`/`.cxx`/`.cc`/`.c++` files
- **Drag-and-drop** support (requires optional `tkinterdnd2` package)
- **Configurable options** — optimization level, `-Wall -Wextra` warnings, extra flags (e.g. `-lm -pthread`)
- **Run after compile** — optionally execute the binary immediately after a successful build
- **Colour-coded output console** — errors in red, warnings in amber, success in green, stdout in lime
- **Non-blocking compilation** — runs the compiler in a background thread so the UI stays responsive
- **Cross-platform** — works on Windows, macOS, and Linux

---

## Requirements

### System

| Dependency | Purpose |
|---|---|
| Python 3.10+ | Required (uses `str \| None` union syntax) |
| `gcc` / `g++` | The actual compiler — must be on your `PATH` |

### Installing GCC / G++

**Windows** — install [MinGW-w64](https://www.mingw-w64.org/) or [MSYS2](https://www.msys2.org/), then add `bin/` to your PATH.

**macOS** — install Xcode Command Line Tools:
```bash
xcode-select --install
```

**Linux (Debian/Ubuntu)**:
```bash
sudo apt install build-essential
```

### Python Packages

Tkinter ships with most Python distributions. The only optional package is for drag-and-drop:

```bash
pip install tkinterdnd2   # optional — enables drag-and-drop
```

---

## Installation

```bash
git clone https://github.com/your-username/c-compiler-gui.git
cd c-compiler-gui

# Optional: create a virtual environment
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

pip install tkinterdnd2        # optional
```

---

## Usage

### Launch the GUI

```bash
python compiler_gui.py
```

### Open with a file pre-loaded

```bash
python compiler_gui.py path/to/your_file.c
```

### Workflow

1. **Load a source file** — drag-and-drop a `.c` or `.cpp` file onto the drop zone, or click it / use the **…** browse button.
2. **Set the output path** — auto-filled based on the source filename; override with the browse button if needed.
3. **Configure options**:
   - Choose an optimisation level (`None`, `-O1`, `-O2`, `-O3`, `-Os`, `-Og`)
   - Toggle `-Wall -Wextra` warnings
   - Add any extra flags (e.g. `-lm`, `-pthread`, `-lfoo`)
   - Check **Run after compile** to execute the binary automatically on success
4. Click **▶ COMPILE** — output appears in the console panel on the right.
5. Click **▷ RUN BINARY** at any time to re-run the last compiled executable.

---

## Options Reference

| Option | Default | Description |
|---|---|---|
| Optimisation | `None` | Compiler optimisation flag (`-O1` … `-Os`) |
| Enable `-Wall -Wextra` | ✔ On | Enables common warning flags |
| Run after compile | ✗ Off | Auto-runs the binary after a successful build |
| Extra flags | *(empty)* | Space-separated flags appended to the compile command |

---

## Output Console

| Colour | Meaning |
|---|---|
| 🟦 Cyan | Compiler command / informational messages |
| 🟩 Green | Compilation succeeded / program exited cleanly |
| 🟥 Red | Errors (compiler errors or non-zero exit) |
| 🟨 Amber | Warnings |
| 🟢 Lime | Program stdout |
| Gray | Dim / miscellaneous compiler output |

---

## Project Structure

```
c-compiler-gui/
├── compiler_gui.py   # Main application (single file)
└── README.md
```

---

## Troubleshooting

**`Compiler 'gcc' not found`**
GCC is not installed or not on your `PATH`. See [Installing GCC / G++](#installing-gcc--g) above.

**Drag-and-drop does nothing**
Install `tkinterdnd2` (`pip install tkinterdnd2`) and relaunch. A notice at the bottom of the sidebar confirms whether it is active.

**`Permission denied` when running binary (macOS/Linux)**
The compiled file may lack execute permission. Run:
```bash
chmod +x path/to/your_binary
```

**Compilation times out**
The compiler has a 60-second timeout. Very large translation units may exceed this.

---

## License

MIT — see `LICENSE` for details.
