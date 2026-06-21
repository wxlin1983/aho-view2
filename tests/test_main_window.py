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


def _make_dir_with_images(dir_path, png_bytes, count):
    dir_path.mkdir()
    for i in range(count):
        (dir_path / f"{i:03d}.png").write_bytes(png_bytes)
    return str(dir_path)


def test_updatemc_decay_uses_old_score_not_clobbered(tmp_path, png_bytes):
    folder = _make_dir_with_images(tmp_path / "folder", png_bytes, 30)
    window = AhoView()
    window.open_axiv(folder)

    distant_pic = window.allaxiv[0].axiv[15]
    distant_pic.score_set(5)
    window._scored = {distant_pic}

    window.updatemc()

    assert distant_pic.score == 29
    assert distant_pic.is_loaded is True


def test_scored_working_set_stays_bounded_with_many_archives(tmp_path, png_bytes):
    library_path = tmp_path / "library"
    library_path.mkdir()
    for name in ["A", "B", "C", "D", "E"]:
        _make_dir_with_images(library_path / name, png_bytes, 20)
    total_pics = 5 * 20

    window = AhoView()
    assert window.open_archives(str(library_path)) == 0

    axiv = window.allaxiv[window.axiv_idx]
    for _ in range(40):
        axiv.mv(-1)
        window.plot()

    # The working set settles to a small equilibrium driven by the decay
    # formula's "30" constant, regardless of how many pictures exist in
    # total across all open archives.
    assert len(window._scored) < total_pics
    assert len(window._scored) <= 30


def test_close_axiv_forgets_pictures(tmp_path, png_bytes):
    folder_a = _make_dir_with_images(tmp_path / "A", png_bytes, 5)
    folder_b = _make_dir_with_images(tmp_path / "B", png_bytes, 5)

    window = AhoView()
    window.open_axiv(folder_a)
    archive_a_pics = list(window.allaxiv[0].axiv)
    window.open_axiv(folder_b)

    assert window.allaxiv[1].axiv_path == folder_a
    window.close_axiv(1)

    assert not any(p in window._scored for p in archive_a_pics)
    assert all(p.is_loaded is False for p in archive_a_pics)
