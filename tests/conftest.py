from __future__ import annotations
import base64
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

# Smallest possible valid PNG (1x1 black pixel), used as a real loadable fixture.
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def valid_image(tmp_path):
    path = tmp_path / "valid.png"
    path.write_bytes(_TINY_PNG)
    return str(path)


@pytest.fixture
def invalid_image(tmp_path):
    path = tmp_path / "invalid.png"
    path.write_text("not an image")
    return str(path)


@pytest.fixture
def png_bytes():
    return _TINY_PNG
