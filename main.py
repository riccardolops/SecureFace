import os
import sys
import time

import cv2
import dlib
import numpy as np
from utils.registration import RegisterWindow
from utils.login import LoginWindow
from Cryptodome.Cipher import AES
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (QApplication, QLineEdit, QGroupBox, QGridLayout,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QComboBox)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("Face authentication app")
        self.setGeometry(0, 0, 300, 100)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)  # noqa: F821
        self.menu_file.addAction(exit)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.button1 = QPushButton("Register")
        self.button2 = QPushButton("Login")
        self.button1.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        buttons_layout.addWidget(self.button2)
        buttons_layout.addWidget(self.button1)

        right_layout = QHBoxLayout()
        right_layout.addLayout(buttons_layout, 1)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(right_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connections
        self.button1.clicked.connect(self.register)
        self.button2.clicked.connect(self.login)

        self._register_window = RegisterWindow()
        self._login_window = LoginWindow()

    @Slot()
    def register(self):
        print("Registering new user...")
        #self.button1.setEnabled(False)
        #self.button2.setEnabled(False)
        self._register_window.show()

    @Slot()
    def login(self):
        print("Logging in...")
        #self.button1.setEnabled(False)
        #self.button2.setEnabled(False)
        self._login_window.refresh_combobox()
        self._login_window.show()
        

if __name__ == "__main__":
    app = QApplication()
    w = MainWindow()
    w.show()
    sys.exit(app.exec())