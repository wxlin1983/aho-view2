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
  — an ordered collection of `Pic`s, built either by scanning a directory for
  image files (`.jpg`, `.jpeg`, `.png`, `.bmp`) or wrapping a single file
  path. Tracks the currently selected index and supports relative
  navigation with wraparound.
- **`AhoView`** ([src/aho_view/gui/main_window.py](src/aho_view/gui/main_window.py))
  — the `QMainWindow`. Holds a list of open `PicAxiv` archives, handles
  keyboard/mouse/drag-and-drop input, and renders the current image into a
  single `QLabel`.

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

## Archives and navigation

`AhoView.allaxiv` is a list of `PicAxiv`, with `axiv_idx` pointing at the
active one. Opening a path (`Ctrl+O` or drag-and-drop) inserts a new
`PicAxiv` at the front of the list and makes it active. `Up`/`Down` cycle
between open archives (wrapping); `Left`/`Right`, `Page Up`/`Page Down`,
`Home`/`End` move within the active archive's picture list (also wrapping).
`offset_idx` on both `AhoView` and `PicAxiv` implement this relative,
wraparound indexing.

## Testing

[tests/](tests/) covers the pure-logic pieces (`Pic`, `PicAxiv`) with
`pytest`, using a tiny real PNG fixture so `QPixmap` loading is exercised
without needing a visible display (`QT_QPA_PLATFORM=offscreen`, set in
[tests/conftest.py](tests/conftest.py)). The GUI class (`AhoView`) is not
currently covered by automated tests — it would need `pytest-qt` or manual
event simulation to drive key/mouse/drag events.
