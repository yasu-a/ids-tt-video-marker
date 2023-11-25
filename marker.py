import json
import os.path

import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class LabelDataFormatError(RuntimeError):
    pass


class LabelData:
    ROOT_DIR = './labels'

    def __init__(self, data):
        self.__data = data

    @classmethod
    def from_name(cls, name):
        path = os.path.join(cls.ROOT_DIR, name + '.json')
        with open(path, 'r') as f:
            data = json.load(f)

        return cls(data)

        # TODO: format check
        # dct = {}
        # for k, v in data.items():
        #     if not re.fullmatch(r'[0-9]', k):
        #         raise LabelDataFormatError('keys of the root node must be a digit')
        #     if not isinstance(v):

    def iter_labels(self):
        for index, data in self.__data.items():
            name, tags = data['name'], data['tags']
            yield index, name, tags

    def index_to_label(self, i):
        return (self.__data.get(str(i)) or {}).get('name')

    def label_to_data(self, label_name):
        for k, v in self.__data.items():
            if v['name'] == label_name:
                return v
        return None

    def index_to_tag(self, label_name, i):
        data = self.label_to_data(label_name)
        if data is None:
            return None
        try:
            tag = data['tags'][i]
        except IndexError:
            return None
        return tag

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
        combo_files.currentIndexChanged.connect(self.__update_file_selection)
        layout.addWidget(combo_files)
        self.__combo_files = combo_files

        w_labels = QWidget(self)
        layout.addWidget(w_labels)
        self.__w_labels = w_labels

    @pyqtSlot(int)
    def load_files(self):
        self.__combo_files.clear()
        for name in LabelData.list_names():
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
        self.__labels = LabelData.from_name(name)
        self.__update_w_labels()


class MarkerWidget(QWidget):
    view_updated = pyqtSignal(dict)

    @classmethod
    def __default_mark_data(cls):
        return {
            'markers': {},
            'tags': {}
        }

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.__output_dir_path = './markdata'
        self.__path = None

        self.__data = None

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

    def get_marker(self, i):
        return self.__data['markers'].get(str(i))

    def get_marker_subtotal(self, i):
        ks = np.array([int(k) for k, v in self.__data['markers'].items()])
        vs = np.array([v for k, v in self.__data['markers'].items()])

        sort_arg = np.argsort(ks)
        ks = ks[sort_arg]
        vs = vs[sort_arg]

        return np.count_nonzero(vs[ks <= i] == self.get_marker(i))

    def get_tags(self, i):
        return tuple(self.__data['tags'].get(str(i)) or [])

    def set_marker(self, i, name):
        if name is None:
            self.remove_marker(i)
        else:
            self.__data['markers'][str(i)] = name
            self.__save()

    def add_tag(self, i, tag_name):
        if self.get_marker(i) is None:
            return
        if str(i) not in self.__data['tags']:
            self.__data['tags'][str(i)] = []
        if tag_name in self.__data['tags'][str(i)]:
            return
        self.__data['tags'][str(i)].append(tag_name)
        self.__save()

    def remove_marker(self, i):
        try:
            del self.__data['markers'][str(i)]
            try:
                del self.__data['tags'][str(i)]
            except KeyError:
                pass
        except KeyError:
            pass
        else:
            self.__save()

    def remove_tag(self, i, tag_name):
        if self.get_marker(i) is None:
            return
        if str(i) not in self.__data['tags']:
            return
        if tag_name not in self.__data['tags'][str(i)]:
            return
        self.__data['tags'][str(i)].remove(tag_name)
        if not self.__data['tags'][str(i)]:
            del self.__data['tags'][str(i)]
        self.__save()

    def find_marker(self, i, direction, n=None):
        ks = np.array([int(k) for k, v in self.__data['markers'].items()])
        arg_sort = np.argsort(ks)
        ks = ks[arg_sort]

        if n is None:
            k = None
        else:
            k = []
        if direction < 0:
            if ks[ks < i].size != 0:
                if n is None:
                    k = ks[ks < i].max()
                else:
                    k = ks[ks < i][ks[ks < i].argsort()[-n:]]
        else:
            if ks[ks > i].size != 0:
                if n is None:
                    k = ks[ks > i].min()
                else:
                    k = ks[ks > i][ks[ks > i].argsort()[:n]]
        return k

    def update_view(self, current_frame_index):
        n_side = 60
        idx = [i for i in range(current_frame_index - n_side, current_frame_index + n_side + 1)]

        dct = {}
        for i in idx:
            marker = self.get_marker(i)
            if marker is not None:
                tags = self.get_tags(i)
                tags = '[' + ','.join(tags) + ']' if tags else ''
                subtotal = self.get_marker_subtotal(i)
                for j, ch in enumerate(f'!{marker}{tags}({subtotal})'):
                    dct[i + j] = ch
        lst_str = ''.join([dct.get(i, '_') for i in idx])
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_stream.setText(lst_str)

        dct = {}
        for i in idx:
            if i % 10 == 0:
                for j, ch in enumerate(f'|_{i}' if i >= 0 else ''):
                    dct[i + j] = ch
        lst_str = ''.join([dct.get(i, '_') for i in idx])
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_tl.setText(lst_str)

        lst_str = ''.join('!' if i == current_frame_index else '_' for i in idx)
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_center.setText(lst_str)

        self.view_updated.emit(self.__data)

    def __load(self, path):
        dir_path = os.path.abspath(os.path.dirname(path))
        os.makedirs(dir_path, exist_ok=True)

        self.__path = path

        if not os.path.exists(self.__path):
            self.__data = self.__default_mark_data()
        else:
            with open(self.__path, 'r') as f:
                self.__data = json.load(f)

    def __save(self):
        with open(self.__path, 'w') as f:
            json.dump(self.__data, f, indent=True, sort_keys=True)

    # noinspection PyUnusedLocal
    @pyqtSlot(str, float, int)
    def setup_meta(self, path, fps, n_fr):
        json_path = os.path.join(
            self.__output_dir_path,
            os.path.splitext(os.path.split(path)[1])[0] + '.json'
        )
        self.__load(json_path)

    # noinspection PyUnusedLocal
    @pyqtSlot(QImage, int, float)
    def setup_frame(self, img, idx, ts):
        self.update_view(idx)
