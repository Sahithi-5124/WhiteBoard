
import sys

from PySide6.QtWidgets import QApplication
from client.ui.main_window import MainWindow


def main():
    # Create the Qt application
    app = QApplication(sys.argv)

    # Create and display the main window
    window = MainWindow()
    window.show()

    # Start the application's event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
