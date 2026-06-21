# Aho View

A simple and fast image viewer built with PySide6.

## Installation

Using [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/wxlin1983/aho-view2.git
cd aho-view2
uv sync
```

## Usage

To run the application:

```bash
uv run aho-view
```

"File" has two ways to open content:

- **View Archives...** (`Ctrl+Alt+O`) — pick a folder that itself contains
  multiple archives (subfolders and/or zip files). Each one becomes a
  separate archive you can switch between with `Up`/`Down`. This replaces
  whatever was previously open.
- **View Archive...** (`Ctrl+O`) — pick a folder, a single image, or a
  `.zip` archive to view as one archive (you'll be asked "Folder..." or
  "File..." to pick the right native dialog). Picking a single image opens
  its containing folder as an archive and starts on that image, so you can
  still browse its siblings. Added to the currently open archives.

Dragging and dropping a folder, image, or zip onto the window behaves like
"View Archive...". Zip archives are treated like a folder of images: a
single top-level folder inside the zip is unwrapped automatically, and
nested zip files are ignored.

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
| `Ctrl+Alt+O` | View archives in a folder |
| `Ctrl+O` | View a single archive (folder/image/zip) |
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
