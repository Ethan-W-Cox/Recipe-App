# custom_title_bar.py
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QLabel, QPushButton, QHBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super(CustomTitleBar, self).__init__()
        self.parent = parent
        self.setFixedHeight(40)
        self.setAutoFillBackground(True)
        self.setPalette(self.create_palette())

        # Title Bar Layout
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Window Title
        self.title = QLabel("YesChef", self)
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title.setStyleSheet("color: white; font: 16pt;")
        self.layout.addWidget(self.title)

        # Spacer to push buttons to the right
        self.layout.addStretch()

        # Minimize Button
        self.minimize_button = QPushButton("_", self)
        self.minimize_button.setFixedSize(40, 40)
        self.minimize_button.setStyleSheet(self.get_button_style())
        self.minimize_button.clicked.connect(self.minimize_window)
        self.layout.addWidget(self.minimize_button)

        # Maximize Button
        self.maximize_button = QPushButton("□", self)
        self.maximize_button.setFixedSize(40, 40)
        self.maximize_button.setStyleSheet(self.get_button_style())
        self.maximize_button.clicked.connect(self.maximize_window)
        self.layout.addWidget(self.maximize_button)

        # Close Button
        self.close_button = QPushButton("x", self)
        self.close_button.setFixedSize(40, 40)
        self.close_button.setStyleSheet(self.get_button_style())
        self.close_button.clicked.connect(self.close_window)
        self.layout.addWidget(self.close_button)

        self.setLayout(self.layout)

    def create_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor(45, 45, 45))
        return palette

    def get_button_style(self):
        return """
        QPushButton {
            background-color: #444;
            color: white;
            border: none;
        }
        QPushButton:hover {
            background-color: #666;
        }
        QPushButton:pressed {
            background-color: #888;
        }
        """

    def close_window(self):
        self.parent.close()

    def minimize_window(self):
        self.parent.showMinimized()

    def maximize_window(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QtCore.QPoint(event.globalPos() - self.old_pos)
        self.parent.move(self.parent.x() + delta.x(), self.parent.y() + delta.y())
        self.old_pos = event.globalPos()
