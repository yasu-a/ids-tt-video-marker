import webbrowser
from typing import Optional, Literal

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import version
from common import DEBUG, FrameAction
from frame import FrameViewWidget
from mark_list import MarkerListWidget
from marker import MarkerWidget, LabelWidget
from video import Video


class HorizontalSplitter(QSplitter):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setOrientation(Qt.Horizontal)

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


class MainWidget(HorizontalSplitter):

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.__video: Optional[Video] = None

        self.__init_ui()
        self.__init_signals()

    def __init_ui(self):
        # b_debug = QPushButton(self)
        # b_debug.clicked.connect(lambda: print(self.find_widget('sd_chooser')))
        # layout.addWidget(b_debug)

        w_label = LabelWidget(self)
        w_label.load_files()
        self.right.addWidget(w_label)
        self.__w_label = w_label

        # marker list
        self.__w_marker_list = MarkerListWidget(self)
        self.__w_marker_list.setMinimumWidth(350)
        self.right.addWidget(self.__w_marker_list)

        # self.right.addStretch(1)

        # frame viewer
        self.__w_frame = FrameViewWidget(self)
        self.left.addWidget(self.__w_frame)

        # marker viewer
        self.__w_marker = MarkerWidget(self)
        self.left.addWidget(self.__w_marker)

        self.left.addStretch(1)

    def __init_signals(self):
        self.__w_frame.control_clicked.connect(self.perform_frame_action)
        self.__w_label.control_clicked.connect(self.perform_marker_action)
        self.__w_marker.view_updated.connect(self.__w_marker_list.update_view)
        self.__w_marker_list.seek_requested.connect(self.__video_seek)

    @pyqtSlot(int)
    def __video_seek(self, i):
        if self.__video is None:
            return
        self.__video.seek(i)

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

        self.__video_seek(i_next)

    @pyqtSlot(int, str)
    def perform_marker_action(self, number: int, marker_type: Literal['label', 'tag']):
        assert isinstance(number, int), number
        assert marker_type in ['label', 'tag'], marker_type

        if self.__video is None:
            return

        i = self.__video.frame_index
        m: MarkerWidget = self.__w_marker
        if marker_type == 'label':
            if number == 0:
                m.remove_marker(i)
            else:
                m_current = m.get_marker(i)
                m_request = self.__w_label.labels.index_to_label(number - 1)
                if m_current == m_request:
                    m.remove_marker(i)
                    m.update_view(i)
                else:
                    m.set_marker(i, m_request)
                    m.update_view(i)
        elif marker_type == 'tag':
            ts_current = m.get_tags(i)
            m_current = m.get_marker(i)
            t_request = self.__w_label.labels.index_to_tag(m_current, number)
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

    # noinspection SpellCheckingInspection
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
        (Qt.NoModifier, Qt.Key_Left): FrameAction.PREV_PAGE,
        (Qt.NoModifier, Qt.Key_Right): FrameAction.NEXT_PAGE
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

    # noinspection PyUnusedLocal
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


# noinspection PyPep8Naming
class MainStatusBarStubs:
    def setStyleSheet(self, ss: str):
        ...


class MainStatusBar(MainStatusBarStubs, QStatusBar):
    clicked = pyqtSignal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

    def showMessage(self, message, p_str=None, color=None, font_weight=None):
        color = color or 'black'
        font_weight = font_weight or 'normal'

        super().showMessage('')
        self.setStyleSheet(f'background-color : {color}; font-weight: {font_weight};')
        super().showMessage(message)

    def mousePressEvent(self, evt):
        self.clicked.emit(self.currentMessage())


# noinspection PyPep8Naming
class MainWindowStubs:
    def setWindowTitle(self, title: str): ...

    def setWindowFlag(self, flag: int): ...

    def setStatusBar(self, sb: QStatusBar): ...

    def setCentralWidget(self, w: QWidget): ...

    def centralWidget(self) -> MainWidget: ...

    def setStyleSheet(self, ss: str): ...

    def menuBar(self) -> QMenuBar: ...

    def statusBar(self) -> MainStatusBar: ...

    def show(self): ...


class MainWindow(QMainWindow, MainWindowStubs):
    file_dropped = pyqtSignal(str)
    key_entered = pyqtSignal(QKeyEvent)

    def __init__(self):
        super().__init__()

        self.__init_ui()
        self.__init_menu_bar()

        self.setGeometry(0, 0, 600, 600)
        self.setWindowTitle(f'Vosaic? {version.app_version_str}')

        if DEBUG:
            self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.__init_signals()

    def __init_ui(self):
        self.setStatusBar(MainStatusBar(self))

        self.setCentralWidget(MainWidget(self))
        QApplication.instance().installEventFilter(self)

    def __menu_action_file_open_video(self):
        # noinspection PyTypeChecker
        video_path, check = QFileDialog.getOpenFileName(
            self,
            '動画ファイルを選択してください',
            '',
            '動画ファイル (*.mp4)'
        )

        if not check:
            return

        w: MainWidget = self.centralWidget()
        w.update_path(video_path)

    # noinspection PyArgumentList
    def __init_menu_bar(self):
        mb = self.menuBar()

        menu = mb.addMenu('&File')

        menu.addAction(
            QAction(
                '&Open Video',
                self,
                triggered=self.__menu_action_file_open_video
            )
        )

        menu.addSeparator()

        menu.addAction(
            QAction(
                '&Exit',
                self,
                triggered=QApplication.quit
            )
        )

        menu = mb.addMenu('&Label')

        menu.addAction(
            QAction(
                '&Export',
                self,
            )
        )

        menu.addAction(
            QAction(
                '&Import',
                self,
            )
        )

    def __init_signals(self):
        w: MainWidget = self.centralWidget()
        self.file_dropped.connect(w.update_path)
        self.key_entered.connect(w.perform_key)

    @staticmethod
    def __extract_dnd_event_path(e):
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

    # noinspection PyPep8Naming
    def __load_mp4_for_debug(self):
        if DEBUG:
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

    @pyqtSlot(str)
    def __statusbar_clicked(self, msg):
        if msg.startswith('アップデートが利用可能です'):
            webbrowser.open(version.latest_version_info['url'])

    # noinspection PyPep8Naming
    def showEvent(self, _):
        self.__load_mp4_for_debug()

        sb: MainStatusBar = self.statusBar()

        if version.update_available:
            sb.clicked.connect(self.__statusbar_clicked)
            sb.showMessage(
                f'アップデートが利用可能です（{version.app_version_str}->{version.latest_version}）'
                f'ここをクリックするとGitHubが開くので　Code -> Download ZIP から最新版をダウンロードしてmarkdataを移行してください。',
                color='pink',
                font_weight='bold'
            )
