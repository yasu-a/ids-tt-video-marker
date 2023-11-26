import re

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout

from labels import LabelDataJson


class LabeledFrameListWidget(QWidget):
    seek_requested = pyqtSignal(int)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        lw = QListWidget(self)
        # noinspection PyUnresolvedReferences
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
            # noinspection PyUnresolvedReferences
            self.seek_requested.emit(i)

    @pyqtSlot(LabelDataJson)
    def update_view(self, data: LabelDataJson):
        self.__lw.clear()

        with data as accessor:
            for fi in accessor.list_labeled_frame_indexes():
                label = accessor.get_label(fi)
                tags = accessor.get_tags(fi)
                count = accessor.get_label_count(fi)
                text = f'{fi:>7d} {label!s:<10s}({count:>3d}) {"/".join(tags)!s}'
                self.__lw.addItem(text)
