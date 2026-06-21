# Aho View — Design

## Overview

Aho View is a PySide6 desktop image viewer organized around three classes:

```
AhoView (gui/main_window.py)
  -> owns a list of PicAxiv  ("archives" — a directory or single file)
       -> owns a list of Pic ("pictures" — one image file each)
```

- **`Pic`** ([src/aho_view/core/pic.py](src/aho_view/core/pic.py)) — a single
  image file on disk. Lazily checks whether the file exists and is a valid
  image, loads/unloads the `QPixmap` data, and produces a scaled `QPixmap`
  for display.
- **`PicAxiv`** ([src/aho_view/core/picaxiv.py](src/aho_view/core/picaxiv.py))
  — an ordered collection of `Pic`s, built by scanning a directory for image
  files (`PIC_FILTERS`), wrapping a single file path, or — if the path is a
  zip file — listing the images inside it (see below). Tracks the currently
  selected index and supports relative navigation with wraparound.
- **`AhoView`** ([src/aho_view/gui/main_window.py](src/aho_view/gui/main_window.py))
  — the `QMainWindow`. Holds a list of open `PicAxiv` archives, handles
  keyboard/mouse/drag-and-drop input, and renders the current image into a
  single `QLabel`.

The package exposes a `main()` entry point in
[src/aho_view/\_\_main\_\_.py](src/aho_view/__main__.py), wired up as the
`aho-view` console script in `pyproject.toml` (`uv run aho-view`).

## Lazy loading and "checked" state

Both `Pic` and `PicAxiv` use a `is_checked` / `is_showable` pair instead of
eagerly validating every file up front:

- `is_checked = False` means "we don't know yet."
- Calling `showable()` performs the check exactly once, caches the result in
  `is_checked`/`is_showable`, and returns the cached value on subsequent
  calls.

This lets `PicAxiv` build its list of `Pic` objects from a directory listing
instantly (without opening every file), and only pay the cost of actually
opening an image (`QPixmap(path)`) when that image is about to be shown or
pre-loaded.

## Predictive pre-loading

`AhoView.updatemc()` (called from `plot()` on every navigation) implements a
simple score-based pre-loading scheme so that flipping through images feels
instant:

1. Every `Pic` has a `score` (float). `score_set` loads the image once the
   score reaches `>= 1` and unloads it once the score drops to `<= 0`.
2. On each navigation, all scores are decayed: `score_set(30 * old/total - 1)`
   — a uniform decay shared across every loaded picture, weighted by their
   current share of the total score. This keeps old/distant images from
   accumulating loaded state forever.
3. The current image, its immediate neighbors (`offset` `-1`, `0`, `+1`), and
   the images 10 steps ahead/behind (matching the `Page Up`/`Page Down`
   hotkeys) each get `+2` added to their score, which is enough to push them
   over the load threshold.

The net effect: the visible image and a small ring of nearby images stay
loaded in memory; everything else is unloaded as you move away from it.

## Scaling modes

`Pic.scale_image(size, pic_rescale_mode)` supports five modes, selected by
`AhoView.pic_rescale_mode`:

| Mode | Behavior |
| --- | --- |
| 0 | Fit within `size`, keep aspect ratio (default) |
| 1 | Original size, no scaling |
| 2 | Stretch to `size`, ignore aspect ratio |
| 3 | Scale to a fixed height, keep aspect ratio |
| 4 | Scale to a fixed width, keep aspect ratio |

Modes 3 and 4 are implemented as a single `KeepAspectRatio` call with one
dimension doubled (`original.scaled(2 * size.width(), size.height(), ...)`
for mode 3). Doubling the dimension that should *not* constrain the result
guarantees Qt's aspect-fit logic is bound by the other dimension instead, so
the image ends up exactly the target height (mode 3) or width (mode 4). This
is a deliberate trick rather than a bug, though it is fragile for extreme
aspect ratios (it assumes the doubled dimension is never actually the
binding constraint).

## Zip archives

`PicAxiv` treats a `.zip` file (detected via `zipfile.is_zipfile`, not just
the extension) like a directory of images:

- `list_zip_image_entries` ([picaxiv.py](src/aho_view/core/picaxiv.py)) reads
  the zip's entry list once (cheap metadata, same cost class as `os.listdir`)
  and applies the same **shallow** semantics as real directories — entries
  nested more than one level deep are ignored, matching the fact that
  `os.listdir` doesn't recurse into subfolders either.
- One exception: if the zip's top level contains nothing but a single
  folder, that folder is transparently unwrapped one level, so the common
  "zip of a single wrapping folder" case still works without requiring users
  to dig into it.
- Nested `.zip` entries and macOS resource-fork junk (`__MACOSX/`, `._*`)
  are always ignored.
- An empty result (no images found) leaves the `PicAxiv` in the same
  `is_checked=True, is_showable=False` state as an empty directory.

Each matching entry becomes a `ZipEntryPic`
([src/aho_view/core/zip_pic.py](src/aho_view/core/zip_pic.py)), a `Pic`
subclass that overrides `resolve_path()` instead of `load()` itself — `Pic`
gained that seam specifically so subclasses can supply a different on-disk
path while keeping `pic_path` as a friendly display string (e.g.
`comic.zip/Comic/page1.png`, shown in the window title). The first time a
`ZipEntryPic` needs to be read, `resolve_path()` decompresses just that one
entry into a per-archive temp directory (`tempfile.mkdtemp`), using a
synthetic `00000.png`-style filename rather than the entry's own name to
avoid zip-slip path traversal from untrusted zip contents. Decompression
therefore happens lazily, driven by the same predictive pre-loading in
`updatemc()` that decides when any other `Pic` gets loaded. Extracted files
stay cached in the temp directory for the archive's lifetime (no
re-extraction as the pre-loader's scores cycle); the whole temp directory is
removed in `PicAxiv.__del__`.

## Archives and navigation

`AhoView.allaxiv` is a list of `PicAxiv`, with `axiv_idx` pointing at the
active one. Opening a single path (`Ctrl+O` or drag-and-drop, via
`open_axiv`) inserts a new `PicAxiv` at the front of the list and makes it
active, leaving any previously open archives in place. `Up`/`Down` cycle
between open archives (wrapping); `Left`/`Right`, `Page Up`/`Page Down`,
`Home`/`End` move within the active archive's picture list (also
wrapping). `offset_idx` on both `AhoView` and `PicAxiv` implement this
relative, wraparound indexing.

`Ctrl+O` ("View Archive...") is one menu action backed by
`open_archive_dialog`, which shows a small `QMessageBox` asking whether to
pick a folder or a file — because a single native `QFileDialog` reliably
selecting *either* a folder or a file turned out not to work in practice.
The chooser just delegates to `open_folder_dialog`/`open_file_dialog`
(plain `QFileDialog.getExistingDirectory`/`getOpenFileName`), both of which
funnel into the same `open_axiv`.

Selecting a plain image file (rather than a folder or zip) doesn't wrap
just that one file — `PicAxiv._init_from_image_file`
([picaxiv.py](src/aho_view/core/picaxiv.py)) scans the image's containing
folder the same way `_init_from_dir` would, and points `pic_idx` at the
selected file, so its siblings stay navigable.

`Ctrl+Alt+O` ("View Archives...", `AhoView.open_archives`) is a separate,
**replacing** flow for browsing a "library": given a folder, module-level
`discover_archives` ([picaxiv.py](src/aho_view/core/picaxiv.py)) builds one
`PicAxiv` per immediate subfolder/zip file that actually contains showable
images (loose images directly in the selected folder are ignored — they
aren't archives themselves), sorted by name, and `open_archives` replaces
`self.allaxiv` outright rather than inserting like `open_axiv` does.

## Testing

[tests/](tests/) covers the pure-logic pieces (`Pic`, `PicAxiv`) with
`pytest`, using a tiny real PNG fixture so `QPixmap` loading is exercised
without needing a visible display (`QT_QPA_PLATFORM=offscreen`, set in
[tests/conftest.py](tests/conftest.py)). The GUI class (`AhoView`) is not
currently covered by automated tests — it would need `pytest-qt` or manual
event simulation to drive key/mouse/drag events.
