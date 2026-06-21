from __future__ import annotations
import os
import zipfile
from .pic import Pic


class ZipEntryPic(Pic):
    """A Pic backed by a single entry inside a zip file.

    Extraction is lazy: the entry is only decompressed (into ``tmp_dir``,
    under a synthetic index-based filename to avoid zip-slip path traversal
    from untrusted entry names) the first time it needs to be read, which
    happens inside ``load()`` via ``resolve_path()``.
    """

    def __init__(self, zip_path: str, entry_name: str, tmp_dir: str, idx: int) -> None:
        super().__init__(pic_path=f"{zip_path}/{entry_name}")
        self.zip_path: str = zip_path
        self.entry_name: str = entry_name
        self.tmp_dir: str = tmp_dir
        self.idx: int = idx
        self._extracted_path: str | None = None

    def resolve_path(self) -> str | None:
        """
        Lazily extracts this zip entry into tmp_dir and returns its path.

        Returns:
            str or None: The extracted file's path, or None on failure.
        """
        if self._extracted_path is not None:
            return self._extracted_path

        ext = os.path.splitext(self.entry_name)[1].lower()
        dest = os.path.join(self.tmp_dir, f"{self.idx:05d}{ext}")
        try:
            with zipfile.ZipFile(self.zip_path) as zf:
                with zf.open(self.entry_name) as src, open(dest, "wb") as out:
                    out.write(src.read())
        except (KeyError, zipfile.BadZipFile, OSError):
            return None

        self._extracted_path = dest
        return self._extracted_path
