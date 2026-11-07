from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QFormLayout
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Configure the main window
        self.setWindowTitle("WhiteBoard")
        self.setMinimumSize(500, 400)

        # Create the central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create the main vertical layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Create the heading
        self.title_label = QLabel("WhiteBoard")
        self.main_layout.addWidget(self.title_label)

        # Create the connection form
        self.form_layout = QFormLayout()

        # Server IP input
        self.host_input = QLineEdit()
        self.host_input.setText("127.0.0.1")
        self.form_layout.addRow("Server IP:", self.host_input)

        # Port input
        self.port_input = QLineEdit()
        self.port_input.setText("5000")
        self.form_layout.addRow("Port:", self.port_input)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.form_layout.addRow("Username:", self.username_input)

        self.main_layout.addLayout(self.form_layout)

        # Create the connect button
        self.connect_button = QPushButton("Connect")
        self.main_layout.addWidget(self.connect_button)
        self.connect_button.clicked.connect(self.handle_connect)

        # Display connection status
        self.status_label = QLabel("Disconnected")
        self.main_layout.addWidget(self.status_label)

    def handle_connect(self):
        self.status_label.setText("Disconnected")

        host = self.host_input.text().strip()
        port = self.port_input.text().strip()
        username = self.username_input.text().strip()

        if not host:
            QMessageBox.warning(self, "Input Error", "Enter server IP address.")
            return

        if not username:
            QMessageBox.warning(self, "Input Error", "Enter your username.")
            return

        try:
            port = int(port)

            if port < 1 or port > 65535:
                raise ValueError

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Enter a valid port number.")
            return

        self.status_label.setText("Inputs validated. Ready to connect.")
