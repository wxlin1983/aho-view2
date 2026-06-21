from __future__ import annotations
import os
import shutil
import tempfile
import zipfile
from PySide6.QtCore import QSize
from .pic import Pic
from .zip_pic import ZipEntryPic

PIC_FILTERS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp",
    ".tiff",
    ".tif",
    ".ico",
    ".svg",
)


def _is_junk_zip_entry(name: str) -> bool:
    """Filters out common non-content zip entries (macOS resource forks)."""
    basename = name.rsplit("/", 1)[-1]
    return name.startswith("__MACOSX/") or basename.startswith("._")


def list_zip_image_entries(zip_path: str) -> list[str]:
    """
    Lists the image entries inside a zip file, treating it like a folder.

    Mirrors the shallow (non-recursive) scanning used for real directories:
    only top-level entries are considered, except that a single top-level
    folder containing everything (and nothing else at the top level) is
    transparently unwrapped one level. Nested zip files are always ignored.

    Args:
        zip_path (str): The path to the zip file.

    Returns:
        list[str]: The matching entry names, as stored in the zip.
    """
    with zipfile.ZipFile(zip_path) as zf:
        names = [
            n
            for n in zf.namelist()
            if not n.endswith("/") and not _is_junk_zip_entry(n)
        ]

    top_level_files = []
    top_level_dirs = set()
    for name in names:
        parts = name.split("/", 1)
        if len(parts) == 1:
            top_level_files.append(name)
        else:
            top_level_dirs.add(parts[0])

    prefix = ""
    if not top_level_files and len(top_level_dirs) == 1:
        prefix = next(iter(top_level_dirs)) + "/"

    entries = []
    for name in names:
        if not name.startswith(prefix):
            continue
        rest = name[len(prefix) :]
        if not rest or "/" in rest:
            continue
        ext = os.path.splitext(rest)[1].lower()
        if ext == ".zip":
            continue
        if ext in PIC_FILTERS:
            entries.append(name)
    return entries


class PicAxiv:
    """Manages a collection of Pic objects, representing a directory of images.

    This class is responsible for scanning a directory for compatible image files
    (e.g., .jpg, .png, .bmp), creating Pic objects for them, and managing the
    current navigation state within the list of images.

    Attributes:
        axiv_path (str): The path to the directory.
        is_checked (bool): Whether the directory has been checked for showable images.
        is_showable (bool): Whether the directory contains any showable images.
        axiv (list[Pic]): The list of Pic objects in the directory.
        pic_idx (int): The index of the current picture in the axiv list.
    """

    def __init__(self, axiv_path: str = "") -> None:
        self.axiv_path: str = axiv_path
        self.is_checked: bool = False
        self.is_showable: bool = False
        self.axiv: list[Pic] = []
        self.pic_idx: int = 0
        self._tmp_dir: str | None = None

        if not os.path.exists(axiv_path):
            self.is_checked = True
            self.is_showable = False
        elif os.path.isdir(axiv_path):
            self._init_from_dir(axiv_path)
        elif zipfile.is_zipfile(axiv_path):
            self._init_from_zip(axiv_path)
        else:
            self._init_from_image_file(axiv_path)

    @staticmethod
    def _scan_dir(dir_path: str) -> list[str]:
        """
        Lists the image files directly inside dir_path (non-recursive).

        Args:
            dir_path (str): The directory to scan.

        Returns:
            list[str]: The matching file names.
        """
        return [
            f
            for f in os.listdir(dir_path)
            if os.path.splitext(f)[1].lower() in PIC_FILTERS
        ]

    def _init_from_dir(self, dir_path: str) -> None:
        """
        Builds the picture list from the images directly inside a directory.

        Args:
            dir_path (str): The path to the directory.
        """
        dir_list = self._scan_dir(dir_path)
        if not dir_list:
            self.is_checked = True
            self.is_showable = False
            return

        self.axiv = [Pic(os.path.join(dir_path, f)) for f in dir_list]
        self.pic_idx = 0

    def _init_from_image_file(self, image_path: str) -> None:
        """
        Builds the picture list from the images in an image's parent folder.

        This lets selecting a single image still allow navigating to its
        sibling images, starting on the selected one.

        Args:
            image_path (str): The path to the selected image file.
        """
        folder = os.path.dirname(image_path) or "."
        dir_list = self._scan_dir(folder)
        if not dir_list:
            self.is_checked = True
            self.is_showable = False
            return

        self.axiv = [Pic(os.path.join(folder, f)) for f in dir_list]
        selected_name = os.path.basename(image_path)
        self.pic_idx = dir_list.index(selected_name) if selected_name in dir_list else 0

    def _init_from_zip(self, zip_path: str) -> None:
        """
        Builds the picture list from the images inside a zip file.

        Args:
            zip_path (str): The path to the zip file.
        """
        entries = list_zip_image_entries(zip_path)
        if not entries:
            self.is_checked = True
            self.is_showable = False
            return

        self._tmp_dir = tempfile.mkdtemp(prefix="aho_view_")
        self.axiv = [
            ZipEntryPic(zip_path, name, self._tmp_dir, idx)
            for idx, name in enumerate(entries)
        ]
        self.pic_idx = 0

    def __del__(self) -> None:
        """Destructor to clean up Pic objects and any extracted temp files."""
        for p in self.axiv:
            del p
        if self._tmp_dir:
            shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def offset_idx(self, offset: int) -> int:
        """
        Calculates a new index based on an offset, with wrapping.

        Args:
            offset (int): The offset from the current index.

        Returns:
            int: The new index.
        """
        if not self.axiv:
            return 0

        new_idx = self.pic_idx
        if offset < 0:
            for _ in range(abs(offset)):
                new_idx -= 1
                if new_idx < 0:
                    new_idx = len(self.axiv) - 1
        elif offset > 0:
            for _ in range(offset):
                new_idx += 1
                if new_idx >= len(self.axiv):
                    new_idx = 0
        return new_idx

    def showable(self) -> bool:
        """
        Checks if the archive contains any showable pictures.

        Prefers the already-selected picture (pic_idx) so that a
        deliberately chosen starting picture, e.g. from
        _init_from_image_file, isn't clobbered; only falls back to the
        first showable picture if that one isn't actually showable.

        Returns:
            bool: True if there is at least one showable picture, False otherwise.
        """
        if self.is_checked:
            return self.is_showable

        if self.axiv[self.pic_idx].showable():
            self.is_showable = True
            self.is_checked = True
            return self.is_showable

        for i, pic in enumerate(self.axiv):
            if pic.showable():
                self.is_showable = True
                self.is_checked = True
                self.pic_idx = i
                return True

        self.is_showable = False
        self.is_checked = True
        return self.is_showable

    def load(self, offset: int) -> bool:
        """
        Loads the picture at the given offset.

        Args:
            offset (int): The offset from the current index.

        Returns:
            bool: The result of the pic.load() call.
        """
        if not self.axiv:
            return False
        return self.axiv[self.offset_idx(offset)].load()

    def scale(self, offset: int, size: QSize, pic_rescale_mode: int) -> bool:
        """
        Scales the picture at the given offset.

        Args:
            offset (int): The offset from the current index.
            size (QSize): The new size for the image.
            pic_rescale_mode (int): The scaling mode to use.

        Returns:
            bool: The result of the pic.scale_image() call.
        """
        if not self.axiv:
            return False
        return self.axiv[self.offset_idx(offset)].scale_image(size, pic_rescale_mode)

    def ptr(self, m: int = 0) -> Pic | None:
        """
        Gets the Pic object at the given offset.

        Args:
            m (int): The offset from the current index.

        Returns:
            Pic or None: The Pic object at the given offset, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        return self.axiv[self.offset_idx(m)]

    def mv(self, m: int = 0) -> Pic | None:
        """
        Moves the current picture index by the given offset.

        Args:
            m (int): The offset to move the index by.

        Returns:
            Pic or None: The new current Pic object, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        self.pic_idx = self.offset_idx(m)
        return self.axiv[self.pic_idx]

    def begin(self) -> Pic | None:
        """
        Moves the current picture index to the beginning of the list.

        Returns:
            Pic or None: The first Pic object, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        self.pic_idx = 0
        return self.axiv[self.pic_idx]

    def end(self) -> Pic | None:
        """
        Moves the current picture index to the end of the list.

        Returns:
            Pic or None: The last Pic object, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        self.pic_idx = len(self.axiv) - 1
        return self.axiv[self.pic_idx]

    def current_pic(self) -> Pic | None:
        """
        Gets the current Pic object.

        Returns:
            Pic or None: The current Pic object, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        return self.axiv[self.pic_idx]


def discover_archives(folder_path: str) -> list[PicAxiv]:
    """
    Discovers archives (subfolders and zip files) inside a folder.

    Treats folder_path as a "library" of archives rather than an archive
    itself: loose image files directly inside folder_path are ignored, only
    immediate subfolders and zip files are considered as candidate archives.

    Args:
        folder_path (str): The path to the folder to scan.

    Returns:
        list[PicAxiv]: The showable archives found, in sorted name order.
    """
    archives = []
    for name in sorted(os.listdir(folder_path)):
        full_path = os.path.join(folder_path, name)
        if os.path.isdir(full_path) or zipfile.is_zipfile(full_path):
            axiv = PicAxiv(full_path)
            if axiv.showable():
                archives.append(axiv)
    return archives
