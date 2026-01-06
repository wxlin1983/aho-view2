
import os
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QSize, Qt


class Pic:
    """Manages a single image file.

    This class represents a single image in the application. It handles loading the
    image data from disk, unloading it to free up memory, and scaling it for
    display. It also manages a 'score' for the image, which is used by the
    application's predictive pre-loading system.
    
    Attributes:
        name (str): The file path of the image.
        score (float): The score of the image, used for pre-loading.
        is_checked (bool): Whether the image has been checked for showability.
        is_showable (bool): Whether the image can be shown (i.e., it exists and is a valid image).
        is_loaded (bool): Whether the image data is currently loaded into memory.
        original (QPixmap): The original, unscaled image data.
        scaled (QPixmap): The scaled image data, ready for display.
    """
    def __init__(self, file_name: str = '') -> None:
        self.name: str = file_name
        self.score: float = 0
        self.is_checked: bool = False
        self.is_showable: bool = False
        self.is_loaded: bool = False
        self.original: QPixmap = QPixmap()
        self.scaled: QPixmap = QPixmap()

    def __del__(self) -> None:
        """Destructor to clean up QPixmap objects."""
        del self.scaled
        del self.original

    def showable(self) -> bool:
        """
        Checks if the picture can be shown.

        This method will trigger a load if the image hasn't been checked yet.
        
        Returns:
            bool: True if the image is showable, False otherwise.
        """
        if not self.is_checked:
            self.load()
        return self.is_showable

    def load(self) -> bool:
        """
        Loads the image from disk into a QPixmap.

        Returns:
            bool: True if the image was loaded successfully, False otherwise.
        """
        if self.is_loaded:
            return True
        if self.is_checked:
            if not self.is_showable:
                return False

        self.is_checked = True
        self.is_showable = False
        if os.path.exists(self.name) and os.path.isfile(self.name):
            self.original = QPixmap(self.name)
            if not self.original.isNull():
                self.is_showable = True
                self.is_loaded = True
                return True
        return False

    def unload(self) -> bool:
        """
        Unloads the image data from memory to free up resources.
        
        Returns:
            bool: Always returns True.
        """
        if self.is_loaded:
            self.original = QPixmap()
            self.scaled = QPixmap()
            self.is_loaded = False
        return True

    def score_add(self, n: float) -> float:
        """
        Adds a value to the image's score.
        
        Args:
            n (float): The value to add to the score.
            
        Returns:
            float: The new score.
        """
        return self.score_set(self.score + n)

    def score_set(self, n: float) -> float:
        """
        Sets the image's score.

        If the score is greater than or equal to 1, the image is loaded.
        If the score is less than or equal to 0, the image is unloaded.

        Args:
            n (float): The new score.
        
        Returns:
            float: The new score.
        """
        self.score = n
        if self.score <= 0:
            self.score = 0
            self.unload()
        elif self.score >= 1:
            self.load()
        return self.score

    def delete_file(self) -> bool:
        """
        Deletes the image file from the filesystem.
        
        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        if self.is_loaded:
            self.unload()
        if os.path.exists(self.name) and os.path.isfile(self.name):
            try:
                os.remove(self.name)
                self.is_showable = False
                return True
            except OSError:
                return False
        return False

    def scale_image(self, size: QSize, pic_rescale_mode: int) -> bool:
        """
        Scales the image to the given size.
        
        Args:
            size (QSize): The new size for the image.
            pic_rescale_mode (int): The scaling mode to use.
                0: Keep aspect ratio, smooth transformation.
                1: Set scaled to original.
                2: Ignore aspect ratio, smooth transformation.
                3: Scaled to height, keep aspect ratio.
                4: Scaled to width, keep aspect ratio.

        Returns:
            bool: True if the image was scaled, False otherwise.
        """
        if not self.showable():
            return False
        if not self.is_loaded:
            self.load()

        # Mode 0: Default scaling.
        # Scales the image to fit within the given size, keeping the aspect ratio.
        # It only rescales if the new size is different from the current scaled size.
        if pic_rescale_mode == 0:
            if (size.height() / size.width() >= self.original.height() / self.original.width()):
                if size.width() == self.scaled.width():
                    return False
            else:
                if size.height() == self.scaled.height():
                    return False
            self.scaled = self.original.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            return True
        # Mode 1: Original size.
        # Sets the scaled image to be the same as the original image.
        elif pic_rescale_mode == 1:
            if self.scaled.size() != self.original.size():
                self.scaled = self.original
                return True
        # Mode 2: Stretched.
        # Scales the image to the given size, ignoring the aspect ratio.
        elif pic_rescale_mode == 2:
            if self.scaled.size() != size:
                self.scaled = self.original.scaled(size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                return True
        # Mode 3: Scale to height.
        # Scales the image to the given height, keeping the aspect ratio.
        elif pic_rescale_mode == 3:
            if self.scaled.height() != size.height():
                self.scaled = self.original.scaled(2 * size.width(), size.height(), Qt.KeepAspectRatio,
                                                     Qt.SmoothTransformation)
                return True
        # Mode 4: Scale to width.
        # Scales the image to the given width, keeping the aspect ratio.
        elif pic_rescale_mode == 4:
            if self.scaled.width() != size.width():
                self.scaled = self.original.scaled(size.width(), 2 * size.height(), Qt.KeepAspectRatio,
                                                     Qt.SmoothTransformation)
                return True
        return False
