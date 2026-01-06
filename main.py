
import sys
from PySide6.QtWidgets import QApplication
from aho_view.gui.main_window import AhoView

def main() -> None:
    """The main entry point of the application."""
    app = QApplication(sys.argv)
    window = AhoView()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
