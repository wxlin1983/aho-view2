from __future__ import annotations
import os
import pytest
from aho_view.core.pic import Pic


def test_load_nonexistent_path_returns_false():
    pic = Pic("/nonexistent/path.png")
    assert pic.load() is False
    assert pic.is_showable is False
    assert pic.is_loaded is False


def test_load_invalid_image_returns_false(invalid_image):
    pic = Pic(invalid_image)
    assert pic.load() is False
    assert pic.is_checked is True
    assert pic.is_showable is False


def test_load_valid_image_returns_true(valid_image):
    pic = Pic(valid_image)
    assert pic.load() is True
    assert pic.is_loaded is True
    assert pic.is_showable is True


def test_showable_triggers_load(valid_image):
    pic = Pic(valid_image)
    assert pic.is_checked is False
    assert pic.showable() is True
    assert pic.is_checked is True


def test_unload_clears_loaded_flag(valid_image):
    pic = Pic(valid_image)
    pic.load()
    assert pic.unload() is True
    assert pic.is_loaded is False


def test_score_set_loads_image_at_threshold(valid_image):
    pic = Pic(valid_image)
    pic.score_set(1)
    assert pic.is_loaded is True


def test_score_set_unloads_image_at_zero(valid_image):
    pic = Pic(valid_image)
    pic.score_set(1)
    pic.score_set(0)
    assert pic.is_loaded is False


def test_score_set_clamps_negative_to_zero(valid_image):
    pic = Pic(valid_image)
    assert pic.score_set(-5) == 0


def test_score_add_accumulates():
    pic = Pic()
    pic.score_set(0.5)
    assert pic.score_add(0.2) == pytest.approx(0.7)


def test_delete_file_removes_existing_file(valid_image):
    pic = Pic(valid_image)
    pic.load()
    assert pic.delete_file() is True
    assert pic.is_showable is False
    assert not os.path.exists(valid_image)


def test_delete_file_missing_returns_false():
    pic = Pic("/nonexistent/path.png")
    assert pic.delete_file() is False
