from __future__ import annotations
from aho_view.gui.main_window import AhoView


def _make_library(library_path, png_bytes):
    library_path.mkdir()

    folder_a = library_path / "A"
    folder_a.mkdir()
    (folder_a / "1.png").write_bytes(png_bytes)

    folder_b = library_path / "B"
    folder_b.mkdir()
    (folder_b / "1.png").write_bytes(png_bytes)

    return str(library_path)


def test_open_archives_replaces_currently_open_archives(tmp_path, png_bytes):
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    (other_dir / "x.png").write_bytes(png_bytes)

    window = AhoView()
    assert window.open_axiv(str(other_dir)) == 0
    assert len(window.allaxiv) == 1

    library = _make_library(tmp_path / "library", png_bytes)
    assert window.open_archives(library) == 0
    assert len(window.allaxiv) == 2
    assert all(other_dir.name not in a.axiv_path for a in window.allaxiv)


def test_open_archives_with_no_archives_leaves_existing_state(tmp_path, png_bytes):
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    (other_dir / "x.png").write_bytes(png_bytes)

    window = AhoView()
    window.open_axiv(str(other_dir))

    empty_library = tmp_path / "empty_library"
    empty_library.mkdir()
    assert window.open_archives(str(empty_library)) == 1
    assert len(window.allaxiv) == 1


def test_open_archives_invalid_path_returns_one():
    window = AhoView()
    assert window.open_archives("/nonexistent/path") == 1
    assert window.open_archives("") == 1
