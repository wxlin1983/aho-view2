from __future__ import annotations
import os
import zipfile
from aho_view.core.picaxiv import discover_archives


def _make_library(tmp_path, png_bytes):
    folder_a = tmp_path / "Trip A"
    folder_a.mkdir()
    (folder_a / "1.png").write_bytes(png_bytes)
    (folder_a / "2.png").write_bytes(png_bytes)

    folder_b = tmp_path / "Trip B"
    folder_b.mkdir()
    (folder_b / "1.jpg").write_bytes(png_bytes)

    empty_folder = tmp_path / "Empty"
    empty_folder.mkdir()

    zip_path = tmp_path / "Trip C.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("1.png", png_bytes)

    (tmp_path / "loose.png").write_bytes(png_bytes)

    return str(tmp_path)


def test_discovers_subfolders_and_zips_in_sorted_order(tmp_path, png_bytes):
    library = _make_library(tmp_path, png_bytes)
    archives = discover_archives(library)
    names = [os.path.basename(a.axiv_path) for a in archives]
    assert names == ["Trip A", "Trip B", "Trip C.zip"]


def test_empty_subfolder_and_loose_images_are_excluded(tmp_path, png_bytes):
    library = _make_library(tmp_path, png_bytes)
    archives = discover_archives(library)
    names = [os.path.basename(a.axiv_path) for a in archives]
    assert "Empty" not in names
    assert "loose.png" not in names
    assert len(archives) == 3


def test_no_archives_found_returns_empty_list(tmp_path):
    (tmp_path / "loose.txt").write_text("hi")
    assert discover_archives(str(tmp_path)) == []
