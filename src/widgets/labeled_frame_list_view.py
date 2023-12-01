import re

from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QHBoxLayout, QCheckBox

from labels import LabelDataJson


class LabeledFrameListWidget(QWidget):
    seek_requested = pyqtSignal(int)

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self.__prev_label_data = None

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        lw = QListWidget(self)
        # noinspection PyUnresolvedReferences
        lw.clicked.connect(lambda: self.__button_clicked('seek'))
        layout.addWidget(lw)
        self.__lw = lw

        cb_reverse_order = QCheckBox('Reverse Order', self)
        # noinspection PyUnresolvedReferences
        cb_reverse_order.stateChanged.connect(self.__cb_reverse_order_updated)
        layout.addWidget(cb_reverse_order)
        self.__cb_reverse_order = cb_reverse_order

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

    @pyqtSlot(int)
    def __cb_reverse_order_updated(self, _):
        self.update_view()

    @pyqtSlot(LabelDataJson)
    def update_view(self, data: LabelDataJson = None):
        if data is None:
            data = self.__prev_label_data
        self.__prev_label_data = data

        self.__lw.clear()

        if data is None:  # skip update if label data has not been given yet
            return

        with data as accessor:
            labeled_frame_index_iter = accessor.list_labeled_frame_indexes()
            if self.__cb_reverse_order.checkState():
                labeled_frame_index_iter = reversed(labeled_frame_index_iter)
            for fi in labeled_frame_index_iter:
                label = accessor.get_label(fi)
                tags = accessor.get_tags(fi)
                count = accessor.get_label_count(fi)
                text = f'{fi:>7d} {label!s:<10s}({count:>3d}) {"/".join(tags)!s}'
                self.__lw.addItem(text)
