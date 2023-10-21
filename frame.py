import functools
import json
import os.path
import sys
import traceback

import cv2
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from video import Video


class FrameViewWidget(QWidget):
    control_clicked = pyqtSignal(str)

    def __init__(self, parent: QObject, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.__fps = -1
        self.__n_fr = -1
        self.__idx = -1
        self.__ts = -1

        self.__view = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # view

        layout_view = QHBoxLayout()
        layout.addLayout(layout_view)

        layout_view.addStretch(1)

        view = QLabel(self, text='IMAGE')
        layout_view.addWidget(view)
        self.__view = view

        layout_view.addStretch(1)

        # info

        layout_info = QHBoxLayout()
        layout.addLayout(layout_info)

        def add_control_button(text):
            b = QPushButton(self, text=text)
            b.setFixedWidth(50)
            b.clicked.connect(lambda *args: self.control_clicked.emit(text))
            layout_info.addWidget(b)

        layout_info.addStretch(1)

        add_control_button('<|')
        add_control_button('<<')
        add_control_button('|<')

        label_info = QLabel(self, text='info')
        layout_info.addWidget(label_info)
        self.__label_info = label_info

        add_control_button('>|')
        add_control_button('>>')
        add_control_button('|>')

        layout_info.addStretch(1)

        layout_control = QHBoxLayout()
        layout.addLayout(layout_control)

        def add_control_button(text):
            b = QPushButton(self, text=text)
            b.setFixedWidth(50)
            b.clicked.connect(lambda *args: self.control_clicked.emit(text))
            layout_control.addWidget(b)

        layout_control.addStretch(1)
        add_control_button('<S')
        add_control_button('<M')
        add_control_button('M>')
        add_control_button('S>')
        layout_control.addStretch(1)

    @pyqtSlot()
    def show_busy(self):
        self.setEnabled(False)

    @pyqtSlot()
    def show_active(self):
        self.setEnabled(True)

    @pyqtSlot(str, float, int)
    def setup_meta(self, path, fps, n_fr):
        self.__fps = fps
        self.__n_fr = n_fr

    def __update_info(self):
        idx, ts, fps, n_fr = self.__idx, self.__ts, self.__fps, self.__n_fr
        self.__label_info.setText(
            f'{int(ts) // 60:3d}:{int(ts) % 60:02d}.{(ts - int(ts)) * 1000:03.0f} ({idx:7d}/{n_fr:7d}) {fps=}'
        )

    @pyqtSlot(QImage, int, float)
    def setup_frame(self, img, idx, ts):
        self.__idx = idx
        self.__ts = ts
        self.__view.setPixmap(QPixmap.fromImage(img))
        self.__update_info()
