import json
import os.path
from typing import Optional

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from labels import LabelDataJson
from res import resolve, Domain


class LabelDataFormatError(RuntimeError):
    pass


class LabelTemplate:
    ROOT_DIR = resolve(Domain.TEMPLATE)

    def __init__(self, json_root):
        self.__json_root = json_root

    @classmethod
    def from_template_name(cls, template_name):
        path = os.path.join(cls.ROOT_DIR, template_name + '.json')
        with open(path, 'r') as f:
            json_root = json.load(f)

        return cls(json_root)

        # TODO: format check
        # dct = {}
        # for k, v in json_root.items():
        #     if not re.fullmatch(r'[0-9]', k):
        #         raise LabelDataFormatError('keys of the root node must be a digit')
        #     if not isinstance(v):

    def iter_labels(self):
        for i, entry in enumerate(self.__json_root):
            name, tags = entry['name'], entry['tags']
            yield i, name, tags

    def index_to_label(self, i):
        try:
            return self.__json_root[i]['name']
        except IndexError:
            return None

    def get_entry_by_label_name(self, label_name):
        for entry in self.__json_root:
            if entry['name'] == label_name:
                return entry
        return None

    def index_to_tag(self, label_name, i):
        entry = self.get_entry_by_label_name(label_name)
        if entry is None:
            return None
        try:
            return entry['tags'][i]
        except IndexError:
            return None

    @classmethod
    def list_names(cls):
        return [
            os.path.splitext(name)[0]
            for name in os.listdir(cls.ROOT_DIR)
            if name.endswith('.json')
        ]


class LabelWidget(QWidget):
    control_clicked = pyqtSignal(int, str)  # n, marker_type

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

    @pyqtSlot(int)
    def load_files(self):
        self.__combo_files.clear()
        for name in LabelTemplate.list_names():
            self.__combo_files.addItem(name)

    def __update_w_labels(self):
        w = self.__w_labels
        self.__w_labels = QWidget(self)
        self.layout().addWidget(self.__w_labels)
        w.deleteLater()

        layout = QVBoxLayout()
        self.__w_labels.setLayout(layout)

        for index, name, tags in self.__labels.iter_labels():
            print(index, name, tags)
            # noinspection PyArgumentList
            b_name = QPushButton(
                parent=self,
                text=f'{name} [{index}]',
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

    @pyqtSlot()
    def on_control_clicked(self):
        a, b = map(int, self.sender().objectName().split(','))
        if b < 0:
            self.control_clicked.emit(a, 'label')
        else:
            self.control_clicked.emit(b, 'tag')

    @pyqtSlot(int)
    def __update_file_selection(self, i):
        name = self.__combo_files.itemText(i)
        self.__labels = LabelTemplate.from_template_name(name)
        self.__update_w_labels()


class MarkerWidget(QWidget):
    view_updated = pyqtSignal(LabelDataJson)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.__output_dir_path = resolve(Domain.MARKDATA)
        self.__json_path = None

        self.__data: Optional[LabelDataJson] = None

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        label_stream = QLabel('STREAM', self)
        label_stream.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_stream)
        self.__label_stream = label_stream

        label_tl = QLabel('TL', self)
        label_tl.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_tl)
        self.__label_tl = label_tl

        label_center = QLabel('C', self)
        label_center.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_center)
        self.__label_center = label_center

    def get_marker(self, fi: int) -> str:
        with self.__data as accessor:
            return accessor.get_label(fi)

    def get_marker_subtotal(self, fi: int) -> Optional[int]:
        with self.__data as accessor:
            return accessor.get_label_count(fi)

    def get_tags(self, fi: int) -> tuple[str, ...]:
        with self.__data as accessor:
            return accessor.get_tags(fi)

    def set_marker(self, fi: int, label_name: str):
        with self.__data as accessor:
            if label_name is None:
                accessor.remove_label(fi)
            else:
                accessor.set_label(fi, label_name)

    def add_tag(self, fi: int, tag_name: str):
        with self.__data as accessor:
            accessor.add_tag(fi, tag_name)

    def remove_marker(self, fi: int):
        with self.__data as accessor:
            accessor.remove_label(fi)

    def remove_tag(self, fi: int, tag_name: str):
        with self.__data as accessor:
            accessor.remove_tag(fi, tag_name)

    def find_marker(self, fi: int, direction: int, n: int = None) -> list[int]:
        with self.__data as accessor:
            return accessor.find_nearest_labeled_index(fi, direction, n)

    def update_view(self, current_frame_index):
        n_side = 80
        frame_indexes = [fi for fi in
                         range(current_frame_index - n_side, current_frame_index + n_side + 1)]

        dct = {}
        # overwrite `current_frame_index` to show central item on top
        for fi in (*frame_indexes, current_frame_index):
            marker = self.get_marker(fi)
            if marker is not None:
                tags = self.get_tags(fi)
                tags = '[' + ','.join(tags) + ']' if tags else ''
                subtotal = self.get_marker_subtotal(fi)
                for j, ch in enumerate(f'!{marker}{tags}({subtotal})'):
                    dct[fi + j] = ch
        lst_str = ''.join([dct.get(i, '_') for i in frame_indexes])
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_stream.setText(lst_str)

        dct = {}
        for fi in frame_indexes:
            if fi % 10 == 0:
                for j, ch in enumerate(f'|_{fi}' if fi >= 0 else ''):
                    dct[fi + j] = ch
        lst_str = ''.join([dct.get(i, '_') for i in frame_indexes])
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_tl.setText(lst_str)

        lst_str = ''.join('!' if i == current_frame_index else '_' for i in frame_indexes)
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_center.setText(lst_str)

        self.view_updated.emit(self.__data)

    # noinspection PyUnusedLocal
    @pyqtSlot(str, float, int)
    def setup_meta(self, video_path, fps, n_fr):
        video_name = os.path.splitext(os.path.split(video_path)[1])[0]
        self.__data = LabelDataJson(video_name=video_name)

    # noinspection PyUnusedLocal
    @pyqtSlot(QImage, int, float)
    def setup_frame(self, img, idx, ts):
        self.update_view(idx)
