from __future__ import annotations
import os
from importlib import resources
from PySide6.QtWidgets import QMainWindow, QLabel, QFileDialog, QMessageBox
from PySide6.QtGui import (
    QIcon,
    QKeySequence,
    QAction,
    QKeyEvent,
    QMouseEvent,
    QDragEnterEvent,
    QDropEvent,
    QResizeEvent,
)
from PySide6.QtCore import Qt

from aho_view.core.pic import Pic
from aho_view.core.picaxiv import PIC_FILTERS, PicAxiv, discover_archives

ICON_PATH = resources.files("aho_view") / "resources" / "ahoviewico.ico"

_FILE_FILTER = (
    "Images and Archives ("
    + " ".join(f"*{ext}" for ext in PIC_FILTERS)
    + " *.zip);;All Files (*)"
)


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

    def __init__(self) -> None:
        super().__init__()

        self.allaxiv: list[PicAxiv] = []
        self.axiv_idx: int = 0
        self._scored: set[Pic] = set()

        self.pic_rescale_mode: int = 0
        self.window_size_mode: int = 0

        self.qimglabel: QLabel = QLabel()
        self.setCentralWidget(self.qimglabel)

        self.help_label = QLabel(
            """
            <font color='white'>
            <h2>Hotkeys</h2>
            <p><b>H</b>: Toggle this help screen</p>
            <p><b>Left/Right Arrow</b>: Next/Previous image</p>
            <p><b>Page Up/Down</b>: Skip 10 images forward/backward</p>
            <p><b>Home/End</b>: Go to the first/last image</p>
            <p><b>Up/Down Arrow</b>: Switch to the previous/next archive</p>
            <p><b>G</b>: Toggle fullscreen</p>
            <p><b>Esc</b>: Clear the image view</p>
            <p><b>Ctrl+Alt+O</b>: View archives in a folder</p>
            <p><b>Ctrl+O</b>: View a single archive (folder/image/zip)</p>
            <p><b>Ctrl+W</b>: Close the current archive</p>
            <p><b>Ctrl+Q</b>: Exit the application</p>
            </font>
            """,
            self,
        )
        self.help_label.setAlignment(Qt.AlignCenter)
        self.help_label.setWordWrap(True)
        self.help_label.show()

        self.create_actions()
        self.create_menus()

        self.setWindowTitle("The AHO Viewer - Help")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.setAcceptDrops(True)
        self.resize(800, 600)
        self._update_help_label_geometry()
        self.setStyleSheet(
            """
            QMainWindow { background-color: black; }
            QMenuBar { background-color: black; color: white; }
            QMenuBar::item:selected { background-color: #444444; }
            QMenu { background-color: black; color: white; }
            QMenu::item:selected { background-color: #444444; }
            """
        )

    def offset_both(self, axivm: int, picm: int) -> Pic | None:
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

    def offset_idx(self, offset: int) -> int:
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

    def change_axiv(self, offset: int) -> int:
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

    def close_axiv(self, offset: int) -> int:
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
            self._forget(self.allaxiv[idx_to_close].axiv)
            del self.allaxiv[idx_to_close]
            if self.axiv_idx >= len(self.allaxiv):
                self.axiv_idx = 0
            self.plot()
        else:
            self._forget(self.allaxiv[0].axiv)
            self.allaxiv.clear()
            self.toggle_plot()
            self.setWindowTitle("The AHO Viewer")
        return 0

    def _forget(self, pics: list[Pic]) -> None:
        """
        Unloads and stops tracking the given pictures' pre-load scores.

        Used when an archive is closed or replaced so its pictures don't
        stay referenced (and loaded in memory) via the pre-load working set.

        Args:
            pics (list[Pic]): The pictures to forget.
        """
        for p in pics:
            p.unload()
            self._scored.discard(p)

    def open_archives_dialog(self) -> int:
        """
        Shows a folder picker and opens the archives found inside it.

        Returns:
            int: 0 if any archives were opened, 1 otherwise.
        """
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Open a folder of archives",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly,
        )
        return self.open_archives(folder_path)

    def open_archives(self, folder_path: str) -> int:
        """
        Replaces the open archives with the ones found inside folder_path.

        Each immediate subfolder or zip file inside folder_path that
        contains showable images becomes its own archive. Loose image files
        directly inside folder_path are ignored. Existing open archives are
        left untouched if folder_path is invalid or no archives are found.

        Args:
            folder_path (str): The path to a folder containing archives.

        Returns:
            int: 0 if any archives were opened, 1 otherwise.
        """
        if not folder_path or not os.path.isdir(folder_path):
            return 1

        archives = discover_archives(folder_path)
        if not archives:
            return 1

        for axiv in self.allaxiv:
            self._forget(axiv.axiv)
        self.allaxiv = archives
        self.axiv_idx = 0
        self.plot()
        return 0

    def open_archive_dialog(self) -> int:
        """
        Lets the user pick a folder or a file, then opens it as one archive.

        Returns:
            int: 0 if an archive was opened, 1 otherwise.
        """
        box = QMessageBox(self)
        box.setWindowTitle("View Archive")
        box.setText("Open a folder, or a single image/zip file?")
        folder_btn = box.addButton("Folder...", QMessageBox.ButtonRole.AcceptRole)
        file_btn = box.addButton("File...", QMessageBox.ButtonRole.AcceptRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()

        clicked = box.clickedButton()
        if clicked is folder_btn:
            return self.open_folder_dialog()
        if clicked is file_btn:
            return self.open_file_dialog()
        return 1

    def open_folder_dialog(self) -> int:
        """
        Shows a folder picker and opens the selected folder as an archive.

        Returns:
            int: 0 if an archive was opened, 1 otherwise.
        """
        axiv_path = QFileDialog.getExistingDirectory(
            self, "Open a folder", os.path.expanduser("~"), QFileDialog.ShowDirsOnly
        )
        return self.open_axiv(axiv_path)

    def open_file_dialog(self) -> int:
        """
        Shows a file picker and opens the selected image or zip as an archive.

        Returns:
            int: 0 if an archive was opened, 1 otherwise.
        """
        axiv_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open an image or zip archive",
            os.path.expanduser("~"),
            _FILE_FILTER,
        )
        return self.open_axiv(axiv_path)

    def open_axiv(self, axiv_path: str = "") -> int:
        """
        Opens a new archive from a axiv_path.

        Args:
            axiv_path (str): The path to a folder, image, or zip archive.

        Returns:
            int: 0 if the archive was opened, 1 otherwise.
        """
        if axiv_path:
            pic_folder = PicAxiv(axiv_path)
            if pic_folder.showable():
                self.allaxiv.insert(0, pic_folder)
                self.axiv_idx = 0
                self.plot()
            return 0
        return 1

    def updatemc(self) -> None:
        """
        Updates the scores of all images and pre-loads/unloads them.

        This method implements the predictive loading mechanism. It adjusts
        the scores of pictures near the current one, and then loads or
        unloads them based on their new scores.

        Only pictures that already have a nonzero score (self._scored) are
        touched here, instead of every picture across every open archive —
        every other picture's score is implicitly 0 already. This keeps the
        cost proportional to the pre-load window, not the total library size.
        """
        total_score = sum(p.score for p in self._scored)
        if total_score > 0:
            for p in list(self._scored):
                old_score = p.score
                p.score_set(30 * (old_score / total_score) - 1)
                if p.score <= 0:
                    self._scored.discard(p)

        tmp_all: set[Pic] = set()

        pic_offsets = [0, 1, -1]
        axiv_offsets = [0]

        for axiv_offset in axiv_offsets:
            for pic_offset in pic_offsets:
                pic = self.offset_both(axiv_offset, pic_offset)
                if pic:
                    tmp_all.add(pic)

        pic = self.offset_both(0, 10)
        if pic:
            tmp_all.add(pic)
        pic = self.offset_both(0, -10)
        if pic:
            tmp_all.add(pic)

        for p in tmp_all:
            p.score_add(2)
            self._scored.add(p)

    def plot(self) -> None:
        """
        Displays the current image.

        This method scales the current image and displays it in the main window.
        It also updates the window title with the image name and triggers the
        predictive loading mechanism.
        """
        if not self.allaxiv:
            return

        self.help_label.hide()
        current_pic = self.allaxiv[self.axiv_idx].current_pic()
        if current_pic and current_pic.showable():
            current_pic.scale_image(self.qimglabel.size(), self.pic_rescale_mode)
            self.qimglabel.setAlignment(Qt.AlignCenter)
            self.qimglabel.setPixmap(current_pic.scaled)
            self.updatemc()
            self.setWindowTitle(current_pic.pic_path)

    def toggle_help(self) -> None:
        """Toggles the help screen."""
        if self.help_label.isVisible():
            self.help_label.hide()
            self.setWindowTitle("The AHO Viewer")
        else:
            self.help_label.show()
            self.setWindowTitle("The AHO Viewer - Help")

    def toggle_plot(self) -> None:
        """Clears the image display."""
        self.qimglabel.clear()

    def toggle_fullscreen(self) -> None:
        """Toggles between fullscreen, maximized, and normal window modes."""
        if self.isFullScreen():
            self.showNormal()
        elif self.isMaximized():
            self.showFullScreen()
        else:
            self.showMaximized()

    def create_menus(self) -> None:
        """Creates the main menu bar."""
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.openarchives_act)
        self.file_menu.addAction(self.openarchive_act)
        self.file_menu.addAction(self.close_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_act)

    def create_actions(self) -> None:
        """Creates the actions for the menu bar."""
        self.openarchives_act = QAction("View &Archives...", self)
        self.openarchives_act.setShortcut("Ctrl+Alt+O")
        self.openarchives_act.triggered.connect(self.open_archives_dialog)

        self.openarchive_act = QAction("View &Archive...", self)
        self.openarchive_act.setShortcut(QKeySequence.Open)
        self.openarchive_act.triggered.connect(self.open_archive_dialog)

        self.close_act = QAction("Close Vie&w...", self)
        self.close_act.setShortcut(QKeySequence.Close)
        self.close_act.triggered.connect(lambda: self.close_axiv(0))

        self.exit_act = QAction("E&xit", self)
        self.exit_act.setShortcut(QKeySequence.Quit)
        self.exit_act.triggered.connect(self.close)

    def _update_help_label_geometry(self) -> None:
        """Resizes the help screen to fill the central widget's area."""
        self.help_label.setGeometry(self.centralWidget().geometry())

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handles the window resize event.

        Args:
            event (QResizeEvent): The resize event.
        """
        self._update_help_label_geometry()
        self.plot()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handles key press events for navigation.

        Args:
            event (QKeyEvent): The key press event.
        """
        if event.key() == Qt.Key_H:
            self.toggle_help()
            return

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

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
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

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Handles drag enter events.

        Args:
            event (QDragEnterEvent): The drag enter event.
        """
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        Handles drop events for opening files.

        Args:
            event (QDropEvent): The drop event.
        """
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            for url in mime_data.urls():
                self.open_axiv(url.toLocalFile())
