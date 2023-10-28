import re
from copy import deepcopy
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


class MarkerListWidget(QWidget):
    seek_requested = pyqtSignal(int)

    def __init__(self, parent: QObject, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        lw = QListWidget(self)
        lw.clicked.connect(lambda: self.__button_clicked('seek'))
        layout.addWidget(lw)
        self.__lw = lw

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        # b_seek = QPushButton(self, text='Seek')
        # b_seek.clicked.connect(lambda: self.__button_clicked('seek'))
        # button_layout.addWidget(b_seek)

    @pyqtSlot(str)
    def __button_clicked(self, command):
        if command == 'seek':
            items = self.__lw.selectedItems()
            if len(items) == 0:
                return
            i = int(re.match(r'\s*(\d+)', items[0].text())[1])
            self.seek_requested.emit(i)

    @pyqtSlot(dict)
    def update_view(self, data):
        markers: dict[int, str] = {int(k): v for k, v in data['markers'].items()}
        tags: dict[int, list[str]] = {int(k): v for k, v in data['tags'].items()}

        self.__lw.clear()

        marker_count: dict[str, int] = {k: 0 for k in markers.values()}
        for i in sorted(markers.keys()):
            marker: str = markers[i]
            tag: list[str] = tags.get(i) or []
            count: int = marker_count[marker]
            self.__lw.addItem(f'{i:>7d} {marker!s:<10s}({count + 1:>3d}) {"/".join(tag)!s}')
            marker_count[marker] += 1
