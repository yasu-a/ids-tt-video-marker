import os.path
from typing import Optional

import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from label_template import LabelTemplate
from labels import LabelDataJson
from res import resolve, Domain
from widgets.tui_label import LayeredTUILabel


class LabelTimelineWidget(QWidget):
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
        # noinspection PyUnresolvedReferences
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

    # noinspection PyArgumentList
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

    # noinspection PyArgumentList
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
