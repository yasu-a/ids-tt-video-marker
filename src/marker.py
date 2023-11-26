import collections
import json
import os.path
from typing import Optional, NamedTuple

import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from frozendict import frozendict

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
            name, tags = entry['name'], entry.get('tags', [])
            yield i, name, tags

    def get_label_name_by_index(self, i) -> Optional[str]:
        try:
            return self.__json_root[i]['name']
        except IndexError:
            return None

    def get_entry_by_label_name(self, label_name):
        for i, name, tags in self.iter_labels():
            if name == label_name:
                return dict(
                    name=name,
                    tags=tags
                )
        return None

    def get_tag_by_index(self, label_name, i) -> Optional[str]:
        entry = self.get_entry_by_label_name(label_name)
        if entry is None:
            return None
        try:
            return entry['tags'][i]
        except IndexError:
            return None

    @classmethod
    def list_template_names(cls):
        return [
            os.path.splitext(name)[0]
            for name in os.listdir(cls.ROOT_DIR)
            if name.endswith('.json')
        ]


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

    # noinspection PyArgumentList
    @pyqtSlot()
    def on_control_clicked(self):
        a, b = map(int, self.sender().objectName().split(','))
        a += 1
        if b < 0:
            self.control_clicked.emit(a, 'label')
        else:
            self.control_clicked.emit(b, 'tag')

    # noinspection PyArgumentList
    @pyqtSlot(int)
    def __update_file_selection(self, i):
        name = self.__combo_files.itemText(i)
        self.__labels = LabelTemplate.from_template_name(name)
        self.__update_w_labels()
        self.template_changed.emit(self.__labels)


class RichText(NamedTuple):
    text: str
    color: Optional[str] = None
    background: Optional[str] = None

    def iter_each_char(self):
        fields = self._asdict()
        for ch in self.text:
            yield RichText(**(fields | dict(text=ch)))

    def format(self, text=None):
        text = text or self.text
        if self.color:
            text = f'<font color={self.color!r}>{text}</font>'
        if self.background:
            text = f'<span style="background-color: {self.background}">{text}</span>'
        return text

    def __decoration_hash(self):
        decoration_field_names = set(self._fields) - {'text'}
        decoration_fields = frozendict(
            (field_names, getattr(self, field_names))
            for field_names in decoration_field_names
        )
        return hash(decoration_fields)

    @classmethod
    def array_to_html(cls, rts: list['RichText']):
        ha = np.array([rt.__decoration_hash() for rt in rts])
        ha_change = ha[1:] != ha[:-1]

        lst = []
        for i in range(len(rts)):
            if i == 0 or ha_change[i - 1]:
                lst.append([])
            lst[-1].append(rts[i])

        body = ''.join(
            rt_lst[0].format(
                text=''.join(
                    rt.text for rt in rt_lst
                )
            ) for rt_lst in lst
        )

        html = f'<html>{body}</html>'

        return html


class LayeredTUILabel(QLabel):

    def __init__(self, *__args):
        super().__init__(*__args)

        # noinspection PyUnresolvedReferences
        self.setStyleSheet(
            'background-color: white; '
            'color: white; '
            'font-size: 3; '
            'font-weight: 600;'
        )

        self.__width = None
        self.__layers: collections.OrderedDict[int, Optional[RichText]] \
            = collections.OrderedDict()

    def setText(self, *args):
        raise ValueError('Unsupported operation')

    def tui_clear(self, width: int):
        self.__width = width
        self.__layers = collections.OrderedDict()

    def tui_write(self, i: int, text: str, **kwargs):
        if 'color' not in kwargs:
            kwargs['color'] = 'black'
        component = RichText(text=text, **kwargs)
        self.__layers[i] = component

    def tui_move_to_top(self, i: int):
        try:
            rt = self.__layers.pop(i)
        except KeyError:
            pass
        else:
            self.__layers[i] = rt

    def tui_commit(self):
        chars = [RichText(text='_')] * self.__width

        for i, rt in self.__layers.items():
            for j, rt_char in enumerate(rt.iter_each_char()):
                if i + j >= len(chars):
                    continue
                chars[i + j] = rt_char
        text = RichText.array_to_html(chars)
        super().setText(text)


class MarkerWidget(QWidget):
    # noinspection PyArgumentList
    view_updated = pyqtSignal(LabelDataJson)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.__output_dir_path = resolve(Domain.MARKDATA)
        self.__json_path = None

        self.__data: Optional[LabelDataJson] = None

        self.__label_names = []
        self.__l_streams = []
        self.__n_side_wide = False

        self.__prev_frame_index = None

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)
        self.setLayout(layout)

        cb_wide = QCheckBox('Wide', self)
        cb_wide.stateChanged.connect(self.__wide_changed)
        layout.addWidget(cb_wide)
        self.__cb_wide = cb_wide

        label_cursor = LayeredTUILabel('C', self)
        label_cursor.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_cursor)
        self.__l_cursor = label_cursor

        label_tl = LayeredTUILabel('TL', self)
        label_tl.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_tl)
        self.__l_timeline = label_tl

    @pyqtSlot(int)
    def __wide_changed(self, state: int):
        self.__n_side_wide = bool(state)
        self.update_view()

    # noinspection PyArgumentList
    @pyqtSlot(LabelTemplate)
    def update_template(self, template: LabelTemplate):
        self.__label_names = [name for i, name, tags in template.iter_labels()]
        self.__update_stream_count(len(self.__label_names))
        self.update_view()

    def __update_stream_count(self, n):
        if len(self.__l_streams) == n:
            return self.__l_streams

        for w_label in self.__l_streams:
            self.layout().removeWidget(w_label)

        self.__l_streams.clear()
        for i in range(n):
            w_label = LayeredTUILabel(f'STREAM {i}', self)
            w_label.setAlignment(Qt.AlignCenter)
            self.layout().addWidget(w_label)
            self.__l_streams.append(w_label)

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

    def update_view(self, current_frame_index=None):
        if current_frame_index is None:
            current_frame_index = self.__prev_frame_index
        self.__prev_frame_index = current_frame_index
        if current_frame_index is None:
            return False

        n_side = 80 if self.__n_side_wide else 55
        frame_indexes = np.array([
            fi for fi in range(
                current_frame_index - n_side,
                current_frame_index + n_side + 1
            )
        ])

        for il, l_stream in enumerate(self.__l_streams):
            target_label_name = self.__label_names[il]
            l_stream.tui_clear(len(frame_indexes))
            for i, fi in enumerate(frame_indexes):
                label_name = self.get_marker(fi)
                if label_name is None or label_name != target_label_name:
                    continue
                tags = self.get_tags(fi)
                tags = '[' + ','.join(tags) + ']' if tags else ''
                subtotal = self.get_marker_subtotal(fi)
                text = f'.[{label_name}({subtotal}){tags}]'
                l_stream.tui_write(
                    i,
                    text,
                    background='#880088' if fi == current_frame_index else '#008800',
                    color='white'
                )
            # noinspection PyArgumentList
            l_stream.tui_move_to_top(current_frame_index - frame_indexes.min())
            l_stream.tui_write(0, target_label_name)
            l_stream.tui_move_to_top(0)
            l_stream.tui_commit()

        self.__l_timeline.tui_clear(len(frame_indexes))
        for i, fi in enumerate(frame_indexes):
            if fi % 10 == 0 and fi >= 0:
                self.__l_timeline.tui_write(
                    i,
                    text=f'|{fi}'.ljust(10, '_'),
                    background='#AAAAAA' if (fi // 10) % 2 else '#DDDDDD'
                )
        self.__l_timeline.tui_commit()

        self.__l_cursor.tui_clear(len(frame_indexes))
        self.__l_cursor.tui_write(current_frame_index - frame_indexes.min(), text='v')
        self.__l_cursor.tui_commit()

        self.view_updated.emit(self.__data)

        return True

    # noinspection PyUnusedLocal, PyArgumentList
    @pyqtSlot(str, float, int)
    def setup_meta(self, video_path, fps, n_fr):
        video_name = os.path.splitext(os.path.split(video_path)[1])[0]
        self.__data = LabelDataJson(video_name=video_name)

    # noinspection PyUnusedLocal, PyArgumentList
    @pyqtSlot(QImage, int, float)
    def setup_frame(self, img, idx, ts):
        self.update_view(idx)
