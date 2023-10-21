from enum import Enum, auto
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

from marker import MarkerWidget, LabelData, LabelWidget
from frame import FrameViewWidget
from video import Video


class HorizontalSplitter(QSplitter):
    def __init__(self, parent: QObject, *args, **kwargs):
        super().__init__(parent, orientation=Qt.Horizontal, *args, **kwargs)

        self.__left = None
        self.__right = None

        self.__init_ui()

    def __init_ui(self):
        w_left = QWidget(self)
        self.addWidget(w_left)

        w_right = QWidget(self)
        self.addWidget(w_right)

        self.__left = QVBoxLayout()
        w_left.setLayout(self.__left)

        self.__right = QVBoxLayout()
        w_right.setLayout(self.__right)

    @property
    def left(self):
        return self.__left

    @property
    def right(self):
        return self.__right


class FrameAction(Enum):
    FIRST_PAGE = ('#first', 'seek')
    LAST_PAGE = ('#last', 'seek')
    NEXT_PAGE = (+1, 'relative', 'seek')
    PREV_PAGE = (-1, 'relative', 'seek')
    NEXT_PAGE_STRIDES = ('#fps', +0.2, 'relative', 'seek')
    PREV_PAGE_STRIDES = ('#fps', -0.2, 'relative', 'seek')
    NEXT_PAGE_SECONDS = ('#fps', +10, 'relative', 'seek')
    PREV_PAGE_SECONDS = ('#fps', -10, 'relative', 'seek')
    NEXT_MARKER = (0, 'relative', 'marked_after', '$LAST_PAGE', 'seek')
    PREV_MARKER = (0, 'relative', 'marked_before', '$FIRST_PAGE', 'seek')

    def parse_request_absolute(self, i_current, n_frames, fps, mark_getter):
        constants = {
            'fps': fps,
            'first': 0,
            'last': n_frames - 1
        }
        acc = None
        for inst in self.value:
            if isinstance(inst, (int, float)):
                num = inst
            elif inst.startswith('#'):
                num = constants.get(inst[1:])
                num = int(round(num, 0))
            else:
                num = None

            if isinstance(inst, str) \
                    and inst.startswith('$') \
                    and inst[1:] in type(self).__members__:
                inst = type(self).__members__[inst[1:]]
                if acc is None:
                    return inst.parse_request_absolute(i_current, n_frames, fps, mark_getter)
            elif acc is None:
                acc = num
            elif num is not None:
                acc = int(acc * num)
            elif inst == 'relative':
                acc = i_current + acc
            elif inst == 'marked_after':
                acc = mark_getter(acc, +1)
            elif inst == 'marked_before':
                acc = mark_getter(acc, -1)
            elif inst == 'seek':
                assert acc is not None, (self, self.value, inst, acc)
                return acc
            else:
                assert False, (self, self.value, inst, acc)

        assert False, (self, self.value, '<EOL>', acc)


class MainWidget(HorizontalSplitter):

    def __init__(self, parent: QObject, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.__video: Video = None

        self.__init_ui()
        self.__init_signals()

    def __init_ui(self):
        # b_debug = QPushButton(self)
        # b_debug.clicked.connect(lambda: print(self.find_widget('sd_chooser')))
        # layout.addWidget(b_debug)

        self.right.addWidget(QLabel(self, text='Label Configuration'))

        w_label = LabelWidget(self)
        w_label.load_files()
        self.right.addWidget(w_label)
        self.__w_label = w_label

        self.right.addStretch(1)

        # frame viewer
        self.__w_frame = FrameViewWidget(self)
        self.__w_frame.control_clicked.connect(self.widget_control_clicked)
        self.left.addWidget(self.__w_frame)

        # marker viewer
        self.__w_marker = MarkerWidget(self)
        self.left.addWidget(self.__w_marker)

        self.left.addStretch(1)

    def __init_signals(self):
        pass

    @pyqtSlot(str)
    def widget_control_clicked(self, val):
        act = {
            '<S': FrameAction.FIRST_PAGE,
            '<M': FrameAction.PREV_MARKER,
            '<|': FrameAction.PREV_PAGE_SECONDS,
            '<<': FrameAction.PREV_PAGE_STRIDES,
            '|<': FrameAction.PREV_PAGE,
            'S>': FrameAction.LAST_PAGE,
            'M>': FrameAction.NEXT_MARKER,
            '|>': FrameAction.NEXT_PAGE_SECONDS,
            '>>': FrameAction.NEXT_PAGE_STRIDES,
            '>|': FrameAction.NEXT_PAGE
        }.get(val)
        self.perform_frame_action(act)

    @pyqtSlot(FrameAction)
    def perform_frame_action(self, act: FrameAction):
        if self.__video is None:
            return

        v = self.__video
        i_next = act.parse_request_absolute(
            i_current=v.frame_index,
            n_frames=v.frame_count,
            fps=v.frame_rate,
            mark_getter=self.__w_marker.find_marker
        )

        self.__video.seek(i_next)

    @pyqtSlot(int)
    def perform_marker_action(self, n, marker_type):
        if self.__video is None:
            return

        i = self.__video.frame_index
        m: MarkerWidget = self.__w_marker
        if marker_type == 'label':
            if n == 0:
                m.remove_marker(i)
            else:
                m_current = m.get_marker(i)
                m_request = self.__w_label.labels.index_to_label(n)
                if m_current == m_request:
                    m.remove_marker(i)
                    m.update_view(i)
                else:
                    m.set_marker(i, m_request)
                    m.update_view(i)
        elif marker_type == 'tag':
            ts_current = m.get_tags(i)
            m_current = m.get_marker(i)
            t_request = self.__w_label.labels.index_to_tag(m_current, n)
            if t_request is not None:
                if t_request in ts_current:
                    m.remove_tag(i, t_request)
                    m.update_view(i)
                else:
                    m.add_tag(i, t_request)
                    m.update_view(i)
        else:
            assert False, marker_type

    __NUMERIC_KEYS = {
        **{getattr(Qt, f'Key_{i}'): i for i in range(10)},
        Qt.Key_Delete: Qt.Key_0
    }

    __TAGGING_KEYS = {
        **{getattr(Qt, f'Key_{ch}'): i for i, ch in enumerate('ZXCVBNM')},
        Qt.Key_Delete: Qt.Key_0
    }

    __FRAME_ACTION_KEYS = {
        (Qt.ControlModifier | Qt.ShiftModifier, Qt.Key_A): FrameAction.FIRST_PAGE,
        (Qt.ControlModifier | Qt.ShiftModifier, Qt.Key_D): FrameAction.LAST_PAGE,
        (Qt.NoModifier, Qt.Key_A): FrameAction.PREV_PAGE,
        (Qt.NoModifier, Qt.Key_D): FrameAction.NEXT_PAGE,
        (Qt.ShiftModifier, Qt.Key_A): FrameAction.PREV_PAGE_STRIDES,
        (Qt.ShiftModifier, Qt.Key_D): FrameAction.NEXT_PAGE_STRIDES,
        (Qt.NoModifier, Qt.Key_S): FrameAction.PREV_PAGE,
        (Qt.NoModifier, Qt.Key_W): FrameAction.NEXT_PAGE,
        (Qt.ShiftModifier, Qt.Key_S): FrameAction.PREV_PAGE_STRIDES,
        (Qt.ShiftModifier, Qt.Key_W): FrameAction.NEXT_PAGE_STRIDES,
        (Qt.ControlModifier, Qt.Key_A): FrameAction.PREV_PAGE_SECONDS,
        (Qt.ControlModifier, Qt.Key_D): FrameAction.NEXT_PAGE_SECONDS,
        (Qt.NoModifier, Qt.Key_Q): FrameAction.PREV_MARKER,
        (Qt.NoModifier, Qt.Key_E): FrameAction.NEXT_MARKER,
        (Qt.NoModifier, Qt.Key_Left): FrameAction.PREV_MARKER,
        (Qt.NoModifier, Qt.Key_Right): FrameAction.NEXT_MARKER
    }

    @pyqtSlot(QKeyEvent)
    def perform_key(self, e):
        key = e.key()
        mod = e.modifiers()

        # numeric key
        key_num = self.__NUMERIC_KEYS.get(key)
        if key_num is not None:
            self.perform_marker_action(key_num, marker_type='label')
            return

        # tagging key
        key_num = self.__TAGGING_KEYS.get(key)
        if key_num is not None:
            self.perform_marker_action(key_num, marker_type='tag')
            return

        # else
        for k, act in self.__FRAME_ACTION_KEYS.items():
            k_mod, k_key = k
            if k_mod == mod and k_key == key:
                self.perform_frame_action(act)
                return

    @pyqtSlot(QImage, int, float)
    def __notice_cache(self, img, idx, ts):
        marker_cache = [
            *self.__w_marker.find_marker(idx, -1, 5),
            *self.__w_marker.find_marker(idx, +1, 5)
        ]
        neighbour_cache = [
            *range(idx - 10, idx + 10)
        ]
        self.__video.request_cache([*marker_cache, *neighbour_cache])

    def __init_video_signals(self, v):
        v.seek_finished.connect(self.__w_frame.setup_frame)
        v.seek_finished.connect(self.__w_marker.setup_frame)
        v.seek_finished.connect(self.__notice_cache)

    def __set_video_instance(self, v: Video):
        self.__init_video_signals(v)
        self.__w_frame.setup_meta(v.path, v.frame_rate, v.frame_count)
        self.__w_marker.setup_meta(v.path, v.frame_rate, v.frame_count)
        self.__video = v

    def __remove_video_instance_if_exists(self):
        if self.__video is not None:
            v = self.__video
            self.__video = None
            v.release()
            v.deleteLater()

    @pyqtSlot(str)
    def update_path(self, path):
        self.__remove_video_instance_if_exists()
        v = Video(self, path)
        self.__set_video_instance(v)
        v.seek(0)


DEBUG = True


class MainWindow(QMainWindow):
    file_dropped = pyqtSignal(str)
    key_entered = pyqtSignal(QKeyEvent)

    def __init__(self):
        super().__init__()

        self.setCentralWidget(MainWidget(self))
        QApplication.instance().installEventFilter(self)

        self.setGeometry(0, 0, 600, 600)
        self.setWindowTitle('vosaic?')

        if DEBUG:
            self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.__init_signals()

    def __init_signals(self):
        w: MainWidget = self.centralWidget()
        self.file_dropped.connect(w.update_path)
        self.key_entered.connect(w.perform_key)

    def __extract_dnd_event_path(self, e):
        if not e.mimeData().hasUrls():
            return None
        urls = e.mimeData().urls()
        if len(urls) != 1:
            return None
        path = urls[0].toLocalFile()
        if path.endswith('.mp4'):
            return path

    def handle_drag_enter(self, e):
        if self.__extract_dnd_event_path(e):
            e.accept()
        else:
            e.ignore()

    def handle_drag_move(self, e):
        if self.__extract_dnd_event_path(e):
            e.accept()
        else:
            e.ignore()

    def handle_drop(self, e):
        path = self.__extract_dnd_event_path(e)
        if path:
            self.file_dropped.emit(path)
            e.accept()
        else:
            e.ignore()

    if DEBUG:
        def showEvent(self, evt):
            self.file_dropped.emit(r'H:\idsttvideos\singles\20230219_03_Narumoto_Ito.mp4')

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if isinstance(source, QWindow):
                self.key_entered.emit(event)
                return True
        elif event.type() == QEvent.DragEnter:
            if isinstance(source, QWindow):
                self.handle_drag_enter(event)
                return True
        elif event.type() == QEvent.DragMove:
            if isinstance(source, QWindow):
                self.handle_drag_move(event)
                return True
        elif event.type() == QEvent.Drop:
            if isinstance(source, QWindow):
                self.handle_drop(event)
                return True
        return super().eventFilter(source, event)
