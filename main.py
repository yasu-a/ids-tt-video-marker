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

    @functools.lru_cache(maxsize=int(128e+6 / (1440 * 1040 * 3 * 1 / (2 * 2))))
    def __read(self, i):
        if self.__prop_frame_index() < i:
            delta = i - self.__prop_frame_index()
            if delta < self.frame_rate * 5:
                for _ in range(delta):
                    self.__grab()
            else:
                self.__seek_at(i)
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
    changed = pyqtSignal(int, float)

    def __init__(self):
        super().__init__()

        self.__view = None

        self.init_ui()

        self.__video_path = None
        self.__reader = None
        self.__current = 0
        self.__processing = False

    @property
    def reader(self):
        return self.__reader

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        label_meta = QLabel(self)
        layout.addWidget(label_meta)
        self.__label_meta = label_meta

        view = QLabel(self, text='IMAGE')
        layout.addWidget(view)
        self.__view = view

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
        ts, idx = self.__reader.frame_time, self.__reader.frame_index

        self.__label_info.setText(
            f'{int(ts) // 60:3d}:{int(ts) % 60:02d}.{(ts - int(ts)) * 1000:03.0f} (#{idx})'
        )

        self.changed.emit(idx, ts)

    def update_frame(self, i):
        if self.__processing:
            return
        self.__processing = True

        if self.__reader is not None:
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

        if key == Qt.Key_Q:
            self.set_frame(delta=-1)
        elif key == Qt.Key_E:
            self.set_frame(delta=+1)
        elif key == Qt.Key_A:
            self.set_frame(delta=-int(self.__video_meta['frame_rate'] / 5))
        elif key == Qt.Key_D:
            self.set_frame(delta=+int(self.__video_meta['frame_rate'] / 5))
        elif key == Qt.Key_Z:
            self.set_frame(delta=-int(self.__video_meta['frame_rate']))
        elif key == Qt.Key_C:
            self.set_frame(delta=+int(self.__video_meta['frame_rate']))


class MarkerViewWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.__path = None

        self.__data = {
            'markers': {}
        }

        self.__init_ui()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        label_stream = QLabel(self, text='STREAM')
        layout.addWidget(label_stream)
        self.__label_stream = label_stream

        label_tl = QLabel(self, text='TL')
        layout.addWidget(label_tl)
        self.__label_tl = label_tl

        label_center = QLabel(self, text='C')
        layout.addWidget(label_center)
        self.__label_center = label_center

    def get_marker(self, i):
        return self.__data['markers'].get(str(i))

    def set_marker(self, i, name):
        if name is None:
            self.remove_marker(i)
        else:
            self.data['markers'][str(i)] = name
            self.save()

    def remove_marker(self, i):
        try:
            del self.data['markers'][str(i)]
        except KeyError:
            pass
        else:
            self.save()

    def find_marker(self, i, direction):
        ks = np.array([int(k) for k, v in self.__data['markers'].items()])
        arg_sort = np.argsort(ks)
        ks = ks[arg_sort]

        k = None
        if direction < 0:
            if ks[ks < i].size != 0:
                k = ks[ks < i].max()
        else:
            if ks[ks > i].size != 0:
                k = ks[ks > i].min()

        return k

    def update_path(self, path):
        self.__path = path
        self.load()

    def update_view(self, current_frame_index):
        n_side = 70
        idx = [i for i in range(current_frame_index - n_side, current_frame_index + n_side + 1)]
        lst = []
        for i in idx:
            lst.append(self.get_marker(i))
        lst_str = ''.join('_' if v is None else v[0] for v in lst)
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_stream.setText(lst_str)

        dct = {}
        for i in idx:
            if i % 10 == 0:
                for j, ch in enumerate(f'|_{i}' if i >= 0 else ''):
                    dct[i + j] = ch
        a = [dct.get(i, '_') for i in idx]
        lst_str = ''.join(a)
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_tl.setText(lst_str)

        lst_str = ''.join('!' if i == current_frame_index else '_' for i in idx)
        lst_str = f'<html><font size="2">{lst_str}</font></html>'
        self.__label_center.setText(lst_str)

    def load(self):
        if not os.path.exists(self.__path):
            return

        with open(self.__path, 'r') as f:
            self.__data = json.load(f)

    def save(self):
        with open(self.__path, 'w') as f:
            json.dump(self.__data, f, indent=True, sort_keys=True)

    @property
    def data(self):
        return self.__data


class MarkerWidget(QWidget):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # source dir
        widget_sd = DirectoryChooserWidget('Source Directory',
                                           os.path.expanduser('H:/idsttvideos/singles'))
        widget_sd.changed.connect(self.update_source_list)
        layout.addWidget(widget_sd)
        self.__widget_sd = widget_sd

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
        widget_img_view.changed.connect(self.widget_img_view_changed)
        layout.addWidget(widget_img_view)
        self.__widget_img_view = widget_img_view

        # marker viewer
        widget_marker = MarkerViewWidget()
        layout.addWidget(widget_marker)
        self.__widget_marker = widget_marker

        # misc
        self.update_source_list()

    @pyqtSlot(int, float)
    def widget_img_view_changed(self, idx, ts):
        self.__widget_marker.update_view(idx)

    LABELS = ['Stay', 'Play', 'Ready', None]
    VAL_KEYS = {getattr(Qt, f'Key_{i}'): i for i in range(10)}

    def on_key_press(self, key):
        self.__widget_img_view.on_key_press(key)

        if self.__widget_img_view.reader is not None:
            i = self.__widget_img_view.reader.frame_index
            if key in self.VAL_KEYS:
                n = self.VAL_KEYS[key] - 1
                try:
                    marker = self.LABELS[n]
                    if marker == self.__widget_marker.get_marker(i):
                        marker = None
                except IndexError:
                    pass
                else:
                    self.__widget_marker.set_marker(i, marker)
                    self.__widget_marker.update_view(i)
            elif key == Qt.Key_Delete:
                self.__widget_marker.remove_marker(i)
                self.__widget_marker.update_view(i)
            elif key == Qt.Key_Backspace:
                self.__widget_marker.remove_marker(i)
                self.__widget_img_view.on_key_press(Qt.Key_Q)
            elif key == Qt.Key_Space:
                self.__widget_img_view.on_key_press(Qt.Key_E)
            elif key == Qt.Key_Left:
                j = self.__widget_marker.find_marker(i, -1)
                if j is None:
                    j = 0
                self.__widget_img_view.set_frame(val=j)
            elif key == Qt.Key_Right:
                j = self.__widget_marker.find_marker(i, +1)
                if j is None:
                    j = self.__widget_img_view.reader.frame_count - 1
                self.__widget_img_view.set_frame(val=j)

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
        self.__widget_marker.update_path(
            os.path.join(self.__widget_wd.path,
                         os.path.splitext(os.path.split(selected_video_path)[1])[0] + '.json')
        )
        self.__widget_marker.update_view(0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setCentralWidget(MarkerWidget(self))
        QApplication.instance().installEventFilter(self)

        self.resize(950, 850)
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
