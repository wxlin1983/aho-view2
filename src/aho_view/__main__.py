from __future__ import annotations
import sys
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from aho_view.gui.main_window import AhoView, ICON_PATH


def main() -> None:
    """The main entry point of the application."""
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = AhoView()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
