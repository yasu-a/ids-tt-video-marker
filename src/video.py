import os.path

import cv2
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from cache import lru_cache


class Video(QObject):
    seek_requested = pyqtSignal(int, int)  # i_current, i_next
    seek_finished = pyqtSignal(QImage, int, float)  # img, idx, ts

    def __init__(self, parent: QObject, path):
        super().__init__(parent)

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
    def path(self):
        return self.__path

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

    @lru_cache(maxsize=int(256e+6 / (1440 * 1040 * 3 * 1 / (2 * 2))))
    def __read(self, i):
        if self.__prop_frame_index() > i:
            self.__seek_at(i)
            self.__grab()
        if self.__prop_frame_index() < i:
            delta = i - self.__prop_frame_index()
            if delta < self.frame_rate * 5:
                for _ in range(delta):
                    self.__grab()
            else:
                self.__seek_at(i)
                self.__grab()

        idx = self.__prop_frame_index()
        ts = self.__prop_frame_timestamp()

        assert i == idx, (i, idx)

        img = self.__retrieve()
        img = cv2.resize(img, None, fx=0.6, fy=0.6)
        img = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888).rgbSwapped()
        return img, idx, ts

    def __len__(self):
        return self.frame_count

    @property
    def first(self):
        return 0

    @property
    def last(self):
        return self.__frame_count - 1

    def seek(self, i):
        i_current, i_next = self.frame_index, i

        self.seek_requested.emit(i_current, i_next)

        i = max(self.first, min(self.last, i))
        img, idx, ts = self.__read(i)
        assert i == idx, (i, idx)
        self.__last_frame_index, self.__last_frame_timestamp = idx, ts

        self.seek_finished.emit(img, idx, ts)

    def release(self):
        if self.__cap is not None:
            self.__cap.release()

    def request_cache(self, idx_lst):
        pass
