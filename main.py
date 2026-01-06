
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog
from PySide6.QtGui import QPainter, QColor, QKeySequence, QAction, QPixmap
from PySide6.QtCore import Qt, QSize

from pic import Pic
from picaxiv import PicAxiv


class AhoView(QMainWindow):
    """The main window of the Aho Viewer application.

    This class defines the main application window and all of its functionality.
    It handles user input (keyboard, mouse, drag-and-drop), manages a list of
    image archives (PicAxiv objects), and displays the images. It also implements
    the predictive image loading mechanism.

    Attributes:
        allaxiv (list[PicAxiv]): A list of all open image archives.
        axiv_idx (int): The index of the currently active image archive.
        pic_rescale_mode (int): The current image scaling mode.
        window_size_mode (int): The current window sizing mode.
        qimglabel (QLabel): The label used to display the image.
    """
    def __init__(self):
        super().__init__()

        self.allaxiv = []
        self.axiv_idx = 0

        self.pic_rescale_mode = 0
        self.window_size_mode = 0

        self.qimglabel = QLabel()
        self.setCentralWidget(self.qimglabel)

        self.create_actions()
        self.create_menus()

        self.setWindowTitle('The AHO Viewer')
        self.setAcceptDrops(True)
        self.resize(800, 600)
        self.setStyleSheet("background-color: black;")


    def offset_both(self, axivm, picm):
        """
        Gets the Pic object at a given offset from the current archive and picture.

        Args:
            axivm (int): The offset from the current archive.
            picm (int): The offset from the current picture within that archive.
        
        Returns:
            Pic or None: The Pic object at the given offset, or None if not found.
        """
        axiv = self.allaxiv[self.offset_idx(axivm)]
        return axiv.ptr(picm)

    def offset_idx(self, offset):
        """
        Calculates a new archive index based on an offset, with wrapping.

        Args:
            offset (int): The offset from the current archive index.
            
        Returns:
            int: The new archive index.
        """
        if not self.allaxiv or len(self.allaxiv) == 1 or offset == 0:
            return self.axiv_idx
        
        tmp_idx = self.axiv_idx
        k = 1 if offset > 0 else -1
        for _ in range(abs(offset)):
            tmp_idx += k
            if tmp_idx >= len(self.allaxiv):
                tmp_idx = 0
            elif tmp_idx < 0:
                tmp_idx = len(self.allaxiv) - 1
        return tmp_idx

    def change_axiv(self, offset):
        """
        Changes the current archive.

        Args:
            offset (int): The offset from the current archive index.
        
        Returns:
            int: 0 if the archive was changed, 1 otherwise.
        """
        if offset == 0 or not self.allaxiv:
            return 1
        
        tmp_idx = self.offset_idx(offset)
        if tmp_idx == self.axiv_idx:
            return 1
        
        self.axiv_idx = tmp_idx
        return 0

    def close_axiv(self, offset):
        """
        Closes the archive at the given offset.

        Args:
            offset (int): The offset from the current archive index.
            
        Returns:
            int: Always returns 0.
        """
        if not self.allaxiv:
            return 0
        
        if len(self.allaxiv) > 1:
            idx_to_close = self.offset_idx(offset)
            del self.allaxiv[idx_to_close]
            if self.axiv_idx >= len(self.allaxiv):
                self.axiv_idx = 0
            self.plot()
        else:
            self.allaxiv.clear()
            self.toggle_plot()
            self.setWindowTitle("The AHO Viewer")
        return 0

    def open_axiv(self, directory):
        """
        Opens a new archive from a directory.

        Args:
            directory (str): The path to the directory. If empty, a dialog will be shown.
        
        Returns:
            int: 0 if the archive was opened, 1 otherwise.
        """
        if not directory:
            directory = QFileDialog.getExistingDirectory(self, "Open a folder", os.path.expanduser("~"), QFileDialog.ShowDirsOnly)

        if directory:
            pic_folder = PicAxiv(directory)
            if pic_folder.showable():
                self.allaxiv.insert(0, pic_folder)
                self.axiv_idx = 0
                self.plot()
            return 0
        return 1
    
    def updatemc(self):
        """
        Updates the scores of all images and pre-loads/unloads them.

        This method implements the predictive loading mechanism. It adjusts the
        scores of all images based on their proximity to the currently viewed
        image, and then loads or unloads them based on their new scores.
        """
        total_score = sum(p.score for axiv in self.allaxiv for p in axiv.axiv)
        if total_score > 0:
            for axiv in self.allaxiv:
                for p in axiv.axiv:
                    p.score_set(30 * (p.score_set(0) / total_score) - 1)

        tmp_all = set()
        
        pic_offsets = [0, 1, -1]
        axiv_offsets = [0]
        
        for axiv_offset in axiv_offsets:
            for pic_offset in pic_offsets:
                pic = self.offset_both(axiv_offset, pic_offset)
                if pic:
                    tmp_all.add(pic)

        pic = self.offset_both(0, 10)
        if pic: tmp_all.add(pic)
        pic = self.offset_both(0, -10)
        if pic: tmp_all.add(pic)

        for p in tmp_all:
            p.score_add(2)

    def plot(self):
        """
        Displays the current image.

        This method scales the current image and displays it in the main window.
        It also updates the window title with the image name and triggers the
        predictive loading mechanism.
        """
        if not self.allaxiv:
            return
        
        current_pic = self.allaxiv[self.axiv_idx].current_pic()
        if current_pic and current_pic.showable():
            current_pic.scale_image(self.qimglabel.size(), self.pic_rescale_mode)
            self.qimglabel.setAlignment(Qt.AlignCenter)
            self.qimglabel.setPixmap(current_pic.scaled)
            self.updatemc()
            self.setWindowTitle(current_pic.name)

    def toggle_plot(self):
        """Clears the image display."""
        self.qimglabel.clear()

    def toggle_fullscreen(self):
        """Toggles between fullscreen, maximized, and normal window modes."""
        if self.isFullScreen():
            self.showNormal()
        elif self.isMaximized():
            self.showFullScreen()
        else:
            self.showMaximized()

    def create_menus(self):
        """Creates the main menu bar."""
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.opendir_act)
        self.file_menu.addAction(self.close_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_act)

    def create_actions(self):
        """Creates the actions for the menu bar."""
        self.opendir_act = QAction("Open &Directory...", self)
        self.opendir_act.setShortcut(QKeySequence.Open)
        self.opendir_act.triggered.connect(self.open_axiv)

        self.close_act = QAction("Close Vie&w...", self)
        self.close_act.setShortcut(QKeySequence.Close)
        self.close_act.triggered.connect(lambda: self.close_axiv(0))

        self.exit_act = QAction("E&xit", self)
        self.exit_act.setShortcut(QKeySequence.Quit)
        self.exit_act.triggered.connect(self.close)

    def resizeEvent(self, event):
        """
        Handles the window resize event.

        Args:
            event (QResizeEvent): The resize event.
        """
        self.plot()

    def keyPressEvent(self, event):
        """
        Handles key press events for navigation.

        Args:
            event (QKeyEvent): The key press event.
        """
        if not self.allaxiv:
            return
        
        axiv = self.allaxiv[self.axiv_idx]
        current_pic_before = axiv.current_pic()

        if event.key() == Qt.Key_Left:
            axiv.mv(1)
        elif event.key() == Qt.Key_Right:
            axiv.mv(-1)
        elif event.key() == Qt.Key_PageUp:
            axiv.mv(-10)
        elif event.key() == Qt.Key_PageDown:
            axiv.mv(10)
        elif event.key() == Qt.Key_End:
            axiv.end()
        elif event.key() == Qt.Key_Home:
            axiv.begin()
        elif event.key() == Qt.Key_Up:
            if self.change_axiv(1) == 0:
                self.plot()
        elif event.key() == Qt.Key_Down:
            if self.change_axiv(-1) == 0:
                self.plot()
        elif event.key() == Qt.Key_Escape:
            self.toggle_plot()
        elif event.key() == Qt.Key_G:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
            return

        if current_pic_before != axiv.current_pic():
            self.plot()

    def mouseReleaseEvent(self, event):
        """
        Handles mouse release events for navigation.

        Args:
            event (QMouseEvent): The mouse release event.
        """
        if not self.allaxiv:
            return

        axiv = self.allaxiv[self.axiv_idx]
        current_pic_before = axiv.current_pic()

        if event.button() == Qt.LeftButton:
            axiv.mv(1)
        elif event.button() == Qt.RightButton:
            axiv.mv(-1)
        else:
            super().mouseReleaseEvent(event)
            return
        
        if current_pic_before != axiv.current_pic():
            self.plot()

    def dragEnterEvent(self, event):
        """
        Handles drag enter events.

        Args:
            event (QDragEnterEvent): The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Handles drop events for opening files.

        Args:
            event (QDropEvent): The drop event.
        """
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                self.open_axiv(url.toLocalFile())

def main():
    """The main entry point of the application."""
    app = QApplication(sys.argv)
    window = AhoView()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
