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


class DirectoryChooserWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QObject, title, default_path, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.__textline = None

        self.init_ui(title, default_path)

    def init_ui(self, title, default_path):
        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(self, text=title))

        line_edit = QLineEdit(self, text=default_path)
        line_edit.setEnabled(False)
        layout.addWidget(line_edit)
        self.__textline = line_edit

        button_select_sd = QPushButton(self, text='...')
        button_select_sd.clicked.connect(self.button_clicked)
        layout.addWidget(button_select_sd)

    def button_clicked(self):
        path = str(QFileDialog.getExistingDirectory(
            self,
            'Select Directory',
            self.__textline.text(),
            QFileDialog.ShowDirsOnly
        ))
        if path:
            self.__textline.setText(path)

        self.changed.emit()

    @property
    def path(self):
        return self.__textline.text()
