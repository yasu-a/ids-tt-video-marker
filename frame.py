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

from common import FrameAction

from video import Video


class FrameViewWidget(QWidget):
    control_clicked = pyqtSignal(FrameAction)

    def __init__(self, parent: QObject, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.__fps = -1
        self.__n_fr = -1
        self.__idx = -1
        self.__ts = -1

        self.__view = None

        self.init_ui()

    CONTROL_ACTIONS = (
        (
            ('<|', FrameAction.PREV_PAGE_SECONDS),
            ('<<', FrameAction.PREV_PAGE_STRIDES),
            ('|<', FrameAction.PREV_PAGE)
        ), (
            ('>|', FrameAction.NEXT_PAGE),
            ('>>', FrameAction.NEXT_PAGE_STRIDES),
            ('|>', FrameAction.NEXT_PAGE_SECONDS)
        ), (
            ('<S', FrameAction.FIRST_PAGE),
            ('<M', FrameAction.PREV_MARKER),
            ('M>', FrameAction.NEXT_MARKER),
            ('S>', FrameAction.LAST_PAGE)
        )
    )

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

        layout_info.addStretch(1)

        def add_control_button(text, act, la):
            b = QPushButton(self, text=text)
            b.setFixedWidth(50)
            b.clicked.connect(lambda *args: self.control_clicked.emit(act))
            la.addWidget(b)

        for text, act in self.CONTROL_ACTIONS[0]:
            add_control_button(text, act, layout_info)

        label_info = QLabel(self, text='info')
        layout_info.addWidget(label_info)
        self.__label_info = label_info

        for text, act in self.CONTROL_ACTIONS[1]:
            add_control_button(text, act, layout_info)

        layout_info.addStretch(1)

        layout_control = QHBoxLayout()
        layout.addLayout(layout_control)

        layout_control.addStretch(1)

        for text, act in self.CONTROL_ACTIONS[2]:
            add_control_button(text, act, layout_control)

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
