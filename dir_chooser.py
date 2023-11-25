from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class DirectoryChooserWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, parent: QWidget, title, default_path):
        super().__init__(parent)

        self.__textline = None

        self.init_ui(title, default_path)

    def init_ui(self, title, default_path):
        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(title, self))

        line_edit = QLineEdit(self)
        line_edit.setText(default_path)
        line_edit.setEnabled(False)
        layout.addWidget(line_edit)
        self.__textline = line_edit

        button_select_sd = QPushButton('...', self)
        button_select_sd.clicked.connect(self.button_clicked)
        layout.addWidget(button_select_sd)

    def button_clicked(self):
        # noinspection PyTypeChecker
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
