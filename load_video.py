# v202310200119

import os
from tqdm import tqdm
import cv2
import numpy as np


def extract_meta(video_path):
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    return dict(
        frame_count=frame_count,
        frame_rate=frame_rate
    )


def extract_frames(video_path, retrieve_interval=None, bar=True, size_limit_megabytes=2000,
                   indexes=None, return_iterator=False):
    if not os.path.exists(video_path):
        raise ValueError('video does not exists', video_path)

    def iter_frames():
        nonlocal indexes

        cap = cv2.VideoCapture(video_path)
        meta = extract_meta(video_path)
        frame_count = meta['frame_count']
        frame_rate = meta['frame_rate']

        if indexes is not None:
            indexes = set(indexes)

        num_ret_frames = 0

        it = range(frame_count)
        if bar:
            it = tqdm(it)

        for i, _ in enumerate(it):
            ret = cap.grab()
            if not ret:
                break

            if indexes is not None and i not in indexes:
                continue
            timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            if retrieve_interval is None or timestamp >= retrieve_interval * num_ret_frames:
                ret, image = cap.retrieve()
                if num_ret_frames == 0:  # first time reading frame
                    if retrieve_interval is not None:
                        estimated_size = image.nbytes * frame_count / frame_rate / retrieve_interval
                    elif indexes is not None:
                        estimated_size = image.nbytes * len(indexes)
                    else:
                        estimated_size = image.nbytes * frame_count
                    if estimated_size > size_limit_megabytes * 1e+6:
                        raise ValueError(
                            f'estimated size {estimated_size / 1e+6:.0f}MB exceeds size limit')
                if not ret:
                    break
                yield image, timestamp
                num_ret_frames += 1

        cap.release()

    if return_iterator:
        return iter_frames()
    else:
        images, timestamps = [], []
        for image, timestamp in iter_frames():
            images.append(image)
            timestamps.append(timestamp)

        images = np.stack(images)
        timestamps = np.array(timestamps)

        return images, timestamps


CACHE_DIR = './cache'
VIDEO_DIR = os.path.expanduser('~/Desktop/idsttvideos/singles')
VIDEO_SHAPE = *(np.array([1040, 1440]) // 4), 3


class Video:
    def __init__(self, video_name):
        self.__cache_path = os.path.join(CACHE_DIR, '{}_' + video_name + '.mmap')
        self.__video_path = os.path.join(VIDEO_DIR, video_name + '.mp4')
        self.__n_frames = None
        self.__fps = None
        self.__frames = None
        self.__timestamps = None

        self.load()

    @property
    def n_frames(self):
        return self.__n_frames

    @property
    def fps(self):
        return self.__fps

    def create_cache(self):
        print(self.__n_frames)
        self.__frames = np.memmap(
            self.__cache_path.format('frames'),
            mode='w+',
            dtype=np.uint8,
            shape=(self.__n_frames, *VIDEO_SHAPE)
        )
        self.__timestamps = np.memmap(
            self.__cache_path.format('timestamps'),
            mode='w+',
            dtype=np.float32,
            shape=self.__n_frames
        )

        it = extract_frames(self.__video_path, return_iterator=True, retrieve_interval=0.1,
                            size_limit_megabytes=150000)
        for i, (fr, ts) in enumerate(it):
            fr = cv2.resize(fr, dsize=(VIDEO_SHAPE[[1]], VIDEO_SHAPE[0]))
            self.__frames[i] = fr
            self.__timestamps[i] = ts

    def load(self):
        meta = extract_meta(self.__video_path)
        assert meta['frame_count'] != 0, self.__video_path
        self.__n_frames = meta['frame_count']
        self.__fps = meta['frame_rate']

        if not os.path.exists(self.__cache_path):
            self.create_cache()
        else:
            self.__frames = np.memmap(
                self.__cache_path.format('frames'),
                mode='r',
                dtype=np.uint8,
                shape=(self.__n_frames, *VIDEO_SHAPE)
            )
            self.__timestamps = np.memmap(
                self.__cache_path.format('timestamps'),
                mode='r',
                dtype=np.float32,
                shape=self.__n_frames
            )

    def __getitem__(self, i):
        return self.__frames[i], self.__timestamps[i]

    def __len__(self):
        return self.__n_frames
