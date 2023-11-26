from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QPushButton, QHBoxLayout

from label_template import LabelTemplate


class LabelTemplateWidget(QWidget):
    # noinspection PyArgumentList
    control_clicked = pyqtSignal(int, str)  # n, marker_type
    # noinspection PyArgumentList
    template_changed = pyqtSignal(LabelTemplate)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.__labels = None

        self.__init_ui()

    @property
    def labels(self):
        return self.__labels

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        combo_files = QComboBox(self)
        # noinspection PyUnresolvedReferences
        combo_files.currentIndexChanged.connect(self.__update_file_selection)
        layout.addWidget(combo_files)
        self.__combo_files = combo_files

        w_labels = QWidget(self)
        layout.addWidget(w_labels)
        self.__w_labels = w_labels

    # noinspection PyArgumentList
    @pyqtSlot(int)
    def load_files(self):
        self.__combo_files.clear()
        for name in LabelTemplate.list_template_names():
            self.__combo_files.addItem(name)

    def __update_w_labels(self):
        w = self.__w_labels
        self.__w_labels = QWidget(self)
        self.layout().addWidget(self.__w_labels)
        w.deleteLater()

        layout = QVBoxLayout()
        self.__w_labels.setLayout(layout)

        for index, name, tags in self.__labels.iter_labels():
            # noinspection PyArgumentList
            b_name = QPushButton(
                parent=self,
                text=f'{name} [{index + 1}]',
                clicked=self.on_control_clicked,
                objectName=f'{index},-1'
            )
            # b_name.setFixedWidth(70 * 3 + 1)
            layout.addWidget(b_name)

            layout_tag = None

            n = 3
            for i, tag in enumerate(tags):
                y, x = i // n, i % n
                if x == 0:
                    if layout_tag is not None:
                        layout_tag.addStretch(1)
                    layout_tag = QHBoxLayout()
                    layout.addLayout(layout_tag)
                # noinspection PyArgumentList
                b_tag = QPushButton(
                    parent=self,
                    text=tag,
                    clicked=self.on_control_clicked,
                    objectName=f'{index},{i}'
                )
                b_tag.setFixedWidth(70)
                layout_tag.addWidget(b_tag)
            if layout_tag is not None:
                layout_tag.addStretch(1)

    # noinspection PyArgumentList
    @pyqtSlot()
    def on_control_clicked(self):
        a, b = map(int, self.sender().objectName().split(','))
        a += 1
        if b < 0:
            # noinspection PyUnresolvedReferences
            self.control_clicked.emit(a, 'label')
        else:
            # noinspection PyUnresolvedReferences
            self.control_clicked.emit(b, 'tag')

    # noinspection PyArgumentList
    @pyqtSlot(int)
    def __update_file_selection(self, i):
        name = self.__combo_files.itemText(i)
        self.__labels = LabelTemplate.from_template_name(name)
        self.__update_w_labels()
        # noinspection PyUnresolvedReferences
        self.template_changed.emit(self.__labels)
