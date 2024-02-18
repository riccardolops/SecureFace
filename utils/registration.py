import os
import sys
import time
import cv2
import dlib
import numpy as np
from Cryptodome.Protocol.KDF import PBKDF2
from utils.utils import shape_to_np
from Cryptodome.Cipher import AES
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (QLineEdit, QGridLayout, QHBoxLayout, QLabel, QMainWindow,
                               QPushButton, QSizePolicy, QVBoxLayout, QWidget)


class WindowPassword(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Encode Biometric Data")
        self.setGeometry(0, 0, 300, 100)
        layout = QGridLayout()
        self.user_obj = QLineEdit()
        layout.addWidget(QLabel("Username:"), 0, 0)
        layout.addWidget(self.user_obj, 0, 1)
        self.user_pwd = QLineEdit()
        self.user_pwd.setEchoMode(QLineEdit.Password)
        self.user_pwd.setMaxLength(32)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.user_pwd, 1, 1)
        self.button_login = QPushButton('Register')
        layout.addWidget(self.button_login, 2, 0, 2, 2)
        self.button_login.clicked.connect(self.on_click)
        self.setLayout(layout)
        self.embeddings = None
    
    @Slot()
    def on_click(self):
        key = self.user_pwd.text().encode('utf-8')
        key = key.ljust(32, b'\0')[:32]
        #key = PBKDF2(self.user_obj.text().encode(), key, 32, count=100000, hmac_hash_module=hashlib.sha256)
        cipher = AES.new(key, AES.MODE_OCB)
        array_bytes = self.embeddings.tobytes()
        ciphertext, tag = cipher.encrypt_and_digest(array_bytes)
        assert len(cipher.nonce) == 15
        
        with open(self.user_obj.text() + ".bin", "wb") as f:
            f.write(tag)
            f.write(cipher.nonce)
            f.write(ciphertext)
        self.close()

class ThreadRegister(QThread):
    updateFrame = Signal(QImage)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.button3 = parent.button3
        self.status = True
        self.cap = True
        self.embeddings = None

    def run(self):
        self.cap = cv2.VideoCapture(0)
        while self.status:
            cascade = cv2.CascadeClassifier(
                os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
            predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")
            face_recognition_model = dlib.face_recognition_model_v1(
                "dlib_face_recognition_resnet_model_v1.dat")
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Reading frame in gray scale to process the pattern
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            detections = cascade.detectMultiScale(gray_frame, scaleFactor=1.1,
                                                  minNeighbors=5, minSize=(30, 30))

            # Drawing green rectangle around the pattern
            for (x, y, w, h) in detections:
                pos_ori = (x, y)
                pos_end = (x + w, y + h)
                color = (0, 255, 0)
                cv2.rectangle(frame, pos_ori, pos_end, color, 2)

            if len(detections) == 0:
                cv2.putText(frame, "Nessun volto rilevato", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                self.button3.setEnabled(False)
            elif len(detections) > 1:
                cv2.putText(frame, "Per favore inquadra solo una persona", (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                self.button3.setEnabled(False)
            else:
                x, y, w, h = detections[0]
                drect = dlib.rectangle(int(x),int(y),int(x+w),int(y+h))
                landmarks = predictor(gray_frame, drect)
                points = shape_to_np(landmarks)
                for i in points:
                    x = i[0]
                    y = i[1]
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
                self.embeddings = np.array(
                    face_recognition_model.compute_face_descriptor(frame, landmarks, 1))
                self.button3.setEnabled(True)

            # Reading the image in RGB to display it
            color_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Creating and scaling QImage
            h, w, ch = color_frame.shape
            img = QImage(color_frame.data, w, h, ch * w, QImage.Format_RGB888)
            scaled_img = img.scaled(640, 480, Qt.KeepAspectRatio)

            # Emit signal
            self.updateFrame.emit(scaled_img)
        sys.exit(-1)

class RegisterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("Register new user")
        self.setGeometry(0, 0, 640, 500)
        self._password_window = WindowPassword()

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

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.button1 = QPushButton("Start")
        self.button2 = QPushButton("Cancel")
        self.button3 = QPushButton("Register new user")
        self.button1.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.button3.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        buttons_layout.addWidget(self.button3)
        buttons_layout.addWidget(self.button2)
        buttons_layout.addWidget(self.button1)

        # Thread in charge of updating the image
        self.th = ThreadRegister(self)
        self.th.finished.connect(self.close)
        self.th.updateFrame.connect(self.setImage)

        right_layout = QHBoxLayout()
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
        self.button2.clicked.connect(self.kill_thread)
        self.button3.clicked.connect(self.newuser)
        self.button2.setEnabled(False)
        self.button3.setEnabled(False)

    @Slot()
    def kill_thread(self):
        print("Finishing...")
        self.button2.setEnabled(False)
        self.button1.setEnabled(True)
        self.th.cap.release()
        cv2.destroyAllWindows()
        self.status = False
        self.th.terminate()
        # Give time for the thread to finish
        time.sleep(1)

    @Slot()
    def start(self):
        print("Starting...")
        self.button2.setEnabled(True)
        self.button1.setEnabled(False)
        self.th.status = True
        self.th.start()

    @Slot()
    def newuser(self):
        print("Registering new user...")
        self.kill_thread()
        self._password_window.embeddings = self.th.embeddings
        self._password_window.show()
        self.button3.setEnabled(False)

    @Slot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))
