import sys

import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import load_video


class ExampleWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.init_ui()

        self.__video = load_video.Video(video_name='20230205_04_Narumoto_Harimoto')
        img = cv2.cvtColor(self.__video[0], cv2.COLOR_BGR2RGB)
        img = QImage(img)
        self.__image_viewer.setPixmap(img)

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.__image_viewer = QLabel(self, text='aa')
        layout.addWidget(self.__image_viewer)

        self.resize(550, 550)
        self.setWindowTitle('sample')
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ew = ExampleWidget()
    sys.exit(app.exec_())
