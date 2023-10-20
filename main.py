import functools
import os.path
import sys
import traceback

import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb, file=sys.stderr)
    QApplication.quit()
    # or QtWidgets.QApplication.exit(0)


sys.excepthook = excepthook

DEFAULT_WORKING_DIR = os.path.expanduser('~/VideoMarkerWorking')


class ApplicationContext:
    def __init__(self):
        self.__working_dir_path = None

    def set_working_dir(self, path):
        self.__working_dir_path = path


class DirectoryChooserWidget(QWidget):
    changed = pyqtSignal()

    def __init__(self, title, default_path):
        super().__init__()

        self.__textline = None

        self.init_ui(title, default_path)

    def init_ui(self, title, default_path):
        layout = QHBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel(self, text=title))

        line_edit = QLineEdit(self, text=default_path)
        line_edit.setEnabled(False)
        layout.addWidget(line_edit)
        self.__textline = line_edit

        button_select_sd = QPushButton(self, text='Choose')
        button_select_sd.clicked.connect(self.button_clicked)
        layout.addWidget(button_select_sd)

    def button_clicked(self):
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


class SeekableVideoReader:
    def __init__(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError('file not found')
        if not os.path.isfile(path) or not path.endswith('.mp4'):
            raise FileNotFoundError('invalid file type')

        self.__path = path

        self.__cap = cv2.VideoCapture(path)
        self.__grab()
        self.__retrieve()
        self.__cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        self.__frame_rate = float(self.__cap.get(cv2.CAP_PROP_FPS))
        self.__frame_count = int(self.__cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.__last_frame_index = None
        self.__last_frame_timestamp = None

    def __grab(self):
        self.__cap.grab()

    def __retrieve(self):
        return self.__cap.retrieve()[1]

    def __seek_at(self, i):
        self.__cap.set(cv2.CAP_PROP_POS_FRAMES, i)

    def __prop_frame_index(self):
        return int(self.__cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1

    def __prop_frame_timestamp(self):
        return float(self.__cap.get(cv2.CAP_PROP_POS_MSEC)) / 1e+3

    @property
    def frame_rate(self):
        return self.__frame_rate

    @property
    def frame_count(self):
        return self.__frame_count

    @property
    def frame_index(self):
        return self.__last_frame_index

    @property
    def frame_time(self):
        return self.__last_frame_timestamp

    @functools.lru_cache(maxsize=int(1440 * 1040 * 3 * 1 / (2 * 2) * (30 * 10)))
    def __read(self, i):
        print('READ')
        if self.__prop_frame_index() < i:
            for _ in range(i - self.__prop_frame_index()):
                self.__grab()
        elif self.__prop_frame_index() > i:
            self.__seek_at(i)
            self.__grab()

        idx = self.__prop_frame_index()
        ts = self.__prop_frame_timestamp()

        img = self.__retrieve()
        img = cv2.resize(img, None, fx=0.5, fy=0.5)
        img = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888).rgbSwapped()
        return idx, ts, img

    def __len__(self):
        return self.frame_count

    def __getitem__(self, i):
        i = max(0, min(self.__frame_count - 1, i))
        idx, ts, img = self.__read(i)
        self.__last_frame_index, self.__last_frame_timestamp = idx, ts
        return img

    def release(self):
        if self.__cap is not None:
            self.__cap.release()


class ImageViewWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.__view = None

        self.init_ui()

        self.__video_path = None
        self.__reader = None
        self.__current = 0
        self.__processing = False

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        view = QLabel(self, text='IMAGE')
        layout.addWidget(view)
        self.__view = view

        label_meta = QLabel(self)
        layout.addWidget(label_meta)
        self.__label_meta = label_meta

        label_info = QLabel(self, text='info')
        layout.addWidget(label_info)
        self.__label_info = label_info

    def init_video(self, path):
        self.__video_path = path
        self.update_cap()

    def load_meta(self):
        self.__video_meta = dict(
            frame_count=self.__reader.frame_count,
            frame_rate=self.__reader.frame_rate
        )

        self.__label_meta.setText('. '.join(f'{k}={v}' for k, v in self.__video_meta.items()))

    def update_cap(self):
        if self.__reader is not None:
            self.__reader.release()

        self.__reader = SeekableVideoReader(self.__video_path)
        self.__current = -1
        self.load_meta()

        self.update_frame(0)

    def update_info(self):
        ts = self.__reader.frame_time
        info = dict(
            ts_text=f'{int(ts) // 60:3d}:{int(ts) % 60:02d}.{(ts - int(ts)) * 1000:03.0f}',
            index=self.__reader.frame_index,
            ts=ts,
        )

        self.__label_info.setText('. '.join(f'{k}={v}' for k, v in info.items()))

    def update_frame(self, i):
        if self.__processing:
            return
        self.__processing = True

        if self.__reader is not None:
            # i = max(0, min(self.__video_meta['frame_count'], i))
            #
            # prev_i = self.__current
            # self.__current = i
            #
            # if prev_i != i:
            #     if prev_i > self.__current:
            #         self.__reader.set(cv2.CAP_PROP_POS_FRAMES, i)
            #         self.__reader.grab()
            #     else:
            #         j = prev_i
            #         while j != i:
            #             self.__reader.grab()
            #             j += 1
            #
            #     _, img = self.__reader.retrieve()
            #     img = cv2.resize(img, None, fx=0.5, fy=0.5)
            #     img = QImage(img.data, img.shape[1], img.shape[0],
            #                  QImage.Format_RGB888).rgbSwapped()
            #     self.__view.setPixmap(QPixmap.fromImage(img))
            #     print(self.__current)
            #     self.update_info()
            print(i)
            img = self.__reader[i]
            self.__view.setPixmap(QPixmap.fromImage(img))
            self.update_info()

        self.__processing = False

    def set_frame(self, *, val=None, delta=None):
        if val is None:
            val = self.__reader.frame_index

        if delta is not None:
            val += delta

        val = int(val)

        self.update_frame(val)

    def on_key_press(self, key):
        if self.__reader is None:
            return

        if key == Qt.Key_Left:
            self.set_frame(delta=-1)
        elif key == Qt.Key_Right:
            self.set_frame(delta=+1)
        elif key == Qt.Key_A:
            self.set_frame(delta=-int(self.__video_meta['frame_rate']))
        elif key == Qt.Key_D:
            self.set_frame(delta=+int(self.__video_meta['frame_rate']))


class MarkerWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # source dir
        widget_wd = DirectoryChooserWidget('Source Directory',
                                           os.path.expanduser('H:/idsttvideos/singles'))
        widget_wd.changed.connect(self.update_source_list)
        layout.addWidget(widget_wd)
        self.__widget_sd = widget_wd

        # working dir
        widget_wd = DirectoryChooserWidget('Working Directory',
                                           os.path.expanduser(r'G:\ids-tt-video-maker-working'))
        widget_wd.changed.connect(self.update_source_list)
        layout.addWidget(widget_wd)
        self.__widget_wd = widget_wd

        # source list
        layout_sl = QVBoxLayout()
        layout.addLayout(layout_sl)

        list_sl = QListWidget(self)
        list_sl.setFixedHeight(100)
        list_sl.clicked.connect(self.list_sl_clicked)
        layout_sl.addWidget(list_sl)
        self.__list_sl = list_sl

        label_meta = QLabel(self)
        layout_sl.addWidget(label_meta)
        self.__label_meta = label_meta

        # image viewer
        widget_img_view = ImageViewWidget()
        layout.addWidget(widget_img_view)
        self.__widget_img_view = widget_img_view

        # misc
        self.update_source_list()

    def on_key_press(self, key):
        self.__widget_img_view.on_key_press(key)

    def update_source_list(self):
        source_root = self.__widget_sd.path
        path_lst = os.listdir(source_root)
        self.__list_sl.clear()
        if os.path.exists(source_root):
            for path in path_lst:
                path = os.path.join(source_root, path)
                if path.endswith('.mp4') and os.path.isfile(path):
                    self.__list_sl.addItem(path)

    def list_sl_clicked(self):
        selected_video_path = self.__list_sl.selectedItems()[0].text()
        self.__widget_img_view.init_video(selected_video_path)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setCentralWidget(MarkerWidget(self))
        QApplication.instance().installEventFilter(self)

        self.resize(900, 750)
        self.setWindowTitle('sample')

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if isinstance(source, QWindow):
                self.centralWidget().on_key_press(event.key())
        return super().eventFilter(source, event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("*{font-size: 12pt; font-family: Consolas;}")
    ew = MainWindow()
    ew.show()
    sys.exit(app.exec_())
