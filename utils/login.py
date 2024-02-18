import os
import sys
import time
import cv2
import dlib
import numpy as np
import hashlib
from utils.utils import shape_to_np
from Cryptodome.Cipher import AES
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (QApplication, QLineEdit, QGroupBox, QGridLayout,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QComboBox)

TOLERANCE = 0.6

class ThreadLogin(QThread):
    updateFrame = Signal(QImage)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.status = True
        self.cap = True
        self.face_features = None

    def run(self):
        self.cap = cv2.VideoCapture(0)
        while self.status:
            cascade = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
            predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
            face_recognition_model = dlib.face_recognition_model_v1("dlib_face_recognition_resnet_model_v1.dat")
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Reading frame in gray scale to process the pattern
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            detections = cascade.detectMultiScale(gray_frame, scaleFactor=1.1,
                                                  minNeighbors=5, minSize=(30, 30))

            # Drawing green rectangle around the pattern
            recognised_face = False
            for (x, y, w, h) in detections:
                pos_ori = (x, y)
                pos_end = (x + w, y + h)
                color = (0, 255, 0)
                cv2.rectangle(frame, pos_ori, pos_end, color, 2)
                drect = dlib.rectangle(int(x),int(y),int(x+w),int(y+h))
                landmarks = predictor(gray_frame, drect)
                face_features_detected = np.array(face_recognition_model.compute_face_descriptor(frame, landmarks, 1)) # maps human faces into 128D vectors where pictures of the same person are mapped near to each other and pictures of different people are mapped far apart
                if np.linalg.norm(self.face_features - face_features_detected) <= TOLERANCE:
                    recognised_face = True
                    break
            
            if recognised_face:
                cv2.putText(frame, "Login effettuato con successo!", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Nessun volto riconosciuto.", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # Reading the image in RGB to display it
            color_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Creating and scaling QImage
            h, w, ch = color_frame.shape
            img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)
            scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)

            # Emit signal
            self.updateFrame.emit(scaled_img)
        sys.exit(-1)

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("Login")
        self.setGeometry(0, 0, 640, 500)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit = QAction("Exit", self, triggered=qApp.quit)  # noqa: F821
        self.menu_file.addAction(exit)

        self.menu_about = self.menu.addMenu("&About")
        about = QAction("About Qt", self, shortcut=QKeySequence(QKeySequence.HelpContents),
                        triggered=qApp.aboutQt)  # noqa: F821
        self.menu_about.addAction(about)

        # Create a label for the display camera
        self.label = QLabel(self)
        self.label.setFixedSize(640, 480)

        # Thread in charge of updating the image
        self.th = ThreadLogin(self)
        self.th.finished.connect(self.close)
        self.th.updateFrame.connect(self.setImage)

        # Model group
        self.group_model = QGroupBox("Insert Username and Password:")
        self.group_model.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        model_layout = QHBoxLayout()

        self.combobox = QComboBox()
        for bin_file in os.listdir(os.curdir):
            if bin_file.endswith(".bin"):
                self.combobox.addItem(bin_file[:-4])

        model_layout.addWidget(QLabel("Username:"), 10)
        model_layout.addWidget(self.combobox, 90)
        model_layout.addWidget(QLabel("Password:"), 10)
        self.user_pwd = QLineEdit()
        self.user_pwd.setEchoMode(QLineEdit.Password)
        self.user_pwd.setMaxLength(32)
        model_layout.addWidget(self.user_pwd)

        self.group_model.setLayout(model_layout)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.button1 = QPushButton("Start")
        self.button1.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        buttons_layout.addWidget(self.button1)

        right_layout = QHBoxLayout()
        right_layout.addWidget(self.group_model, 1)
        right_layout.addLayout(buttons_layout, 1)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(right_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connections
        self.button1.clicked.connect(self.start)

    def refresh_combobox(self):
        self.combobox.clear()
        for bin_file in os.listdir(os.curdir):
            if bin_file.endswith(".bin"):
                self.combobox.addItem(bin_file[:-4])

    @Slot()
    def kill_thread(self):
        print("Finishing...")
        self.button1.setEnabled(True)
        self.th.cap.release()
        cv2.destroyAllWindows()
        self.status = False
        self.th.terminate()
        # Give time for the thread to finish
        time.sleep(1)

    @Slot()
    def start(self):
        print("Logging in...")
        with open(self.combobox.currentText() + '.bin', "rb") as f:
            tag = f.read(16)
            nonce = f.read(15)
            ciphertext = f.read()

        key = self.user_pwd.text().encode()
        key = key.ljust(32, b'\0')[:32]
        cipher = AES.new(key, AES.MODE_OCB, nonce=nonce)
        try:
            array_bytes_decrypted = cipher.decrypt_and_verify(ciphertext, tag)
            array_back = np.frombuffer(array_bytes_decrypted, dtype=np.float64).reshape((128,))
            self.th.face_features = array_back
            self.button1.setEnabled(False)
            self.th.start()
        except ValueError:
            print("Wrong password! or File corrupted!")
            return
            

    @Slot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))
