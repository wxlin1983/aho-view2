# Aho View

A simple and fast image viewer built with PySide6.

## Installation

Using [uv](https://docs.astral.sh/uv/) (recommended, also installs dev tools):

```bash
git clone https://github.com/wxlin1983/aho-view2.git
cd aho-view2
uv sync
```

Or with pip:

```bash
git clone https://github.com/wxlin1983/aho-view2.git
cd aho-view2
pip install -r requirements.txt
```

## Usage

To run the application:

```bash
cd src
python main.py
```

(or `uv run python src/main.py` from the repo root)

Open a directory or image file via "File" -> "Open Archive...", or by
dragging and dropping a directory/file onto the window. Each opened
directory or file becomes an "archive" that you can navigate and switch
between.

### Hotkeys

| Key | Action |
| --- | --- |
| `H` | Toggle the help screen |
| `Left` / `Right` | Next / previous image |
| `Page Up` / `Page Down` | Skip 10 images backward / forward |
| `Home` / `End` | Go to the first / last image |
| `Up` / `Down` | Switch to the previous / next archive |
| `G` | Toggle fullscreen |
| `Esc` | Clear the image view |
| `Ctrl+O` | Open a new archive |
| `Ctrl+W` | Close the current archive |
| `Ctrl+Q` | Exit the application |

Left/right mouse click also advance to the next/previous image.

## Development

See [DESIGN.md](DESIGN.md) for an overview of the architecture.

```bash
uv run pytest        # run the test suite
uv run ruff check .  # lint
uv run ruff format . # format
```
