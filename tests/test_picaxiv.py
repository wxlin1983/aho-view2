from __future__ import annotations
import os
from aho_view.core.picaxiv import PicAxiv


def _make_dir(tmp_path, png_bytes, names):
    pic_exts = (".jpg", ".jpeg", ".png", ".bmp")
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    for name in names:
        path = images_dir / name
        if os.path.splitext(name)[1].lower() in pic_exts:
            path.write_bytes(png_bytes)
        else:
            path.write_text("not a picture")
    return str(images_dir)


def test_scans_directory_and_filters_by_extension(tmp_path, png_bytes):
    dir_path = _make_dir(
        tmp_path, png_bytes, ["a.png", "b.jpg", "c.txt", "d.bmp", "readme.md"]
    )
    axiv = PicAxiv(dir_path)
    names = sorted(os.path.basename(p.pic_path) for p in axiv.axiv)
    assert names == ["a.png", "b.jpg", "d.bmp"]


def test_empty_directory_is_not_showable(tmp_path):
    axiv = PicAxiv(str(tmp_path))
    assert axiv.showable() is False


def test_nonexistent_path_is_not_showable():
    axiv = PicAxiv("/nonexistent/path")
    assert axiv.showable() is False


def test_single_file_path_is_loaded(valid_image):
    axiv = PicAxiv(valid_image)
    assert len(axiv.axiv) == 1
    assert axiv.axiv[0].pic_path == valid_image


def test_offset_idx_wraps_forward(tmp_path, png_bytes):
    dir_path = _make_dir(tmp_path, png_bytes, ["a.png", "b.png", "c.png"])
    axiv = PicAxiv(dir_path)
    axiv.pic_idx = 2
    assert axiv.offset_idx(1) == 0


def test_offset_idx_wraps_backward(tmp_path, png_bytes):
    dir_path = _make_dir(tmp_path, png_bytes, ["a.png", "b.png", "c.png"])
    axiv = PicAxiv(dir_path)
    axiv.pic_idx = 0
    assert axiv.offset_idx(-1) == 2


def test_mv_updates_current_pic(tmp_path, png_bytes):
    dir_path = _make_dir(tmp_path, png_bytes, ["a.png", "b.png"])
    axiv = PicAxiv(dir_path)
    start = axiv.current_pic()
    moved = axiv.mv(1)
    assert moved is not start
    assert axiv.current_pic() is moved


def test_begin_and_end(tmp_path, png_bytes):
    dir_path = _make_dir(tmp_path, png_bytes, ["a.png", "b.png", "c.png"])
    axiv = PicAxiv(dir_path)
    axiv.pic_idx = 1
    assert axiv.begin() is axiv.axiv[0]
    assert axiv.end() is axiv.axiv[-1]
