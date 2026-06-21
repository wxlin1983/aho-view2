from __future__ import annotations
import gc
import os
import zipfile
from aho_view.core.picaxiv import PicAxiv
from aho_view.core.zip_pic import ZipEntryPic


def _make_zip(tmp_path, entries: dict[str, bytes], name: str = "archive.zip") -> str:
    zip_path = tmp_path / name
    with zipfile.ZipFile(zip_path, "w") as zf:
        for entry_name, data in entries.items():
            zf.writestr(entry_name, data)
    return str(zip_path)


def test_top_level_images_are_listed_and_loadable(tmp_path, png_bytes):
    zip_path = _make_zip(tmp_path, {"a.png": png_bytes, "b.jpg": png_bytes})
    axiv = PicAxiv(zip_path)
    names = sorted(p.entry_name for p in axiv.axiv)
    assert names == ["a.png", "b.jpg"]

    pic = axiv.axiv[0]
    assert isinstance(pic, ZipEntryPic)
    assert pic.load() is True
    extracted = pic.resolve_path()
    assert extracted is not None
    assert os.path.exists(extracted)


def test_zip_with_no_images_is_not_showable(tmp_path):
    zip_path = _make_zip(tmp_path, {"readme.txt": b"hello", "notes.md": b"hi"})
    axiv = PicAxiv(zip_path)
    assert axiv.showable() is False
    assert axiv.axiv == []


def test_single_top_level_folder_is_unwrapped(tmp_path, png_bytes):
    zip_path = _make_zip(
        tmp_path,
        {"Comic/a.png": png_bytes, "Comic/b.png": png_bytes},
    )
    axiv = PicAxiv(zip_path)
    names = sorted(p.entry_name for p in axiv.axiv)
    assert names == ["Comic/a.png", "Comic/b.png"]
    assert axiv.axiv[0].load() is True


def test_nested_zip_entry_is_ignored(tmp_path, png_bytes):
    zip_path = _make_zip(
        tmp_path,
        {"a.png": png_bytes, "inner.zip": b"not a real zip but irrelevant"},
    )
    axiv = PicAxiv(zip_path)
    names = [p.entry_name for p in axiv.axiv]
    assert names == ["a.png"]


def test_deeply_nested_entry_ignored_when_top_level_has_other_content(
    tmp_path, png_bytes
):
    zip_path = _make_zip(
        tmp_path,
        {"top.png": png_bytes, "sub/deep/a.png": png_bytes},
    )
    axiv = PicAxiv(zip_path)
    names = [p.entry_name for p in axiv.axiv]
    assert names == ["top.png"]


def test_macos_junk_entries_do_not_block_unwrap(tmp_path, png_bytes):
    zip_path = _make_zip(
        tmp_path,
        {
            "Comic/a.png": png_bytes,
            "__MACOSX/Comic/._a.png": png_bytes,
        },
    )
    axiv = PicAxiv(zip_path)
    names = [p.entry_name for p in axiv.axiv]
    assert names == ["Comic/a.png"]


def test_closing_zip_archive_removes_temp_dir(tmp_path, png_bytes):
    zip_path = _make_zip(tmp_path, {"a.png": png_bytes})
    axiv = PicAxiv(zip_path)
    tmp_dir = axiv._tmp_dir
    assert tmp_dir is not None
    axiv.axiv[0].load()
    assert os.path.isdir(tmp_dir)

    del axiv
    gc.collect()
    assert not os.path.exists(tmp_dir)
