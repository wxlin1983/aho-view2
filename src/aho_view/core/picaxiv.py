
import os
from typing import List, Optional
from PySide6.QtCore import QSize
from .pic import Pic


class PicAxiv:
    """Manages a collection of Pic objects, representing a directory of images.

    This class is responsible for scanning a directory for compatible image files
    (e.g., .jpg, .png, .bmp), creating Pic objects for them, and managing the
    current navigation state within the list of images.

    Attributes:
        name (str): The path to the directory.
        is_checked (bool): Whether the directory has been checked for showable images.
        is_showable (bool): Whether the directory contains any showable images.
        axiv (list[Pic]): The list of Pic objects in the directory.
        pic_idx (int): The index of the current picture in the axiv list.
    """
    def __init__(self, file_name: str = '') -> None:
        self.name: str = file_name
        self.is_checked: bool = False
        self.is_showable: bool = False
        self.axiv: List[Pic] = []
        self.pic_idx: int = 0

        pic_filters = ['.jpg', '.jpeg', '.png', '.bmp']

        if os.path.exists(file_name):
            if os.path.isdir(file_name):
                dir_list = [f for f in os.listdir(file_name) if os.path.splitext(f)[1].lower() in pic_filters]
                if not dir_list:
                    self.is_checked = True
                    self.is_showable = False
                    return

                self.axiv = [Pic(os.path.join(file_name, f)) for f in dir_list]
                self.pic_idx = 0
            elif os.path.isfile(file_name):
                self.axiv = [Pic(file_name)]
                self.pic_idx = 0
        else:
            self.is_checked = True
            self.is_showable = False

    def __del__(self) -> None:
        """Destructor to clean up Pic objects."""
        for p in self.axiv:
            del p

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

        Returns:
            bool: True if there is at least one showable picture, False otherwise.
        """
        if self.is_checked:
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

    def ptr(self, m: int = 0) -> Optional[Pic]:
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

    def mv(self, m: int = 0) -> Optional[Pic]:
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

    def begin(self) -> Optional[Pic]:
        """
        Moves the current picture index to the beginning of the list.
        
        Returns:
            Pic or None: The first Pic object, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        self.pic_idx = 0
        return self.axiv[self.pic_idx]

    def end(self) -> Optional[Pic]:
        """
        Moves the current picture index to the end of the list.
        
        Returns:
            Pic or None: The last Pic object, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        self.pic_idx = len(self.axiv) - 1
        return self.axiv[self.pic_idx]

    def current_pic(self) -> Optional[Pic]:
        """
        Gets the current Pic object.
        
        Returns:
            Pic or None: The current Pic object, or None if the archive is empty.
        """
        if not self.axiv:
            return None
        return self.axiv[self.pic_idx]
