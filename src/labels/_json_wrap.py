import codecs
import json
import os.path
import zipfile
from typing import Optional, Union

import numpy as np
from PyQt5.QtCore import QMutex

import labels
import machine
from res import resolve, Domain

MARKDATA_PATH = resolve(Domain.MARKDATA)


def export_all(dst_path):
    os.makedirs(dst_path, exist_ok=True)

    zf_path = os.path.join(dst_path, f'iDSTTVideoMarkerData_{machine.platform_hash_digest}.zip')

    with zipfile.ZipFile(zf_path, 'w') as zf:
        for json_name in os.listdir(MARKDATA_PATH):
            json_path = os.path.join(MARKDATA_PATH, json_name)
            with codecs.open(json_path, 'rb') as f_json:
                with zf.open(json_name, 'w') as f_zipped_file:
                    # noinspection PyTypeChecker
                    f_zipped_file.write(f_json.read())


# When upgrade version, make sure you ...
#  - edit LabelDataJson.VERSION = <new-version>
#  - re-implement the default-producer LabelDataJson.__default_json()
#  - add the new entry to JSON_STRUCTURE in label_data_json_compat.py
#  - add function `_upgrade_<previous-version>_to_<new-version>` in label_data_json_compat.py
class LabelDataJson:
    VERSION = 2

    @classmethod
    def __default_json(cls, video_name):
        return labels.compat.create_default(
            version=cls.VERSION,
            params=dict(
                video_name=video_name
            )
        )

    def __init__(self, video_name):
        self.__video_name = video_name

        self.__json_root = None
        self.__current_accessor = None

        self.__lock = QMutex()

    @property
    def json_path(self):
        return os.path.join(
            MARKDATA_PATH,
            f'{self.__video_name}.json'
        )

    def __load_json(self):
        if os.path.exists(self.json_path):
            with codecs.open(self.json_path, 'r', encoding='utf-8') as f:
                json_root = json.load(f)
            json_root = labels.compat.convert(
                json_path=self.json_path,
                json_root=json_root
            )
            self.__json_root = json_root
        else:
            self.__json_root = self.__default_json(self.__video_name)

    @property
    def __jr(self):
        if self.__json_root is None:
            self.__load_json()

        return self.__json_root

    def dump(self):
        if self.__json_root is None:
            return

        json_dir_path = os.path.dirname(self.json_path)
        os.makedirs(json_dir_path, exist_ok=True)
        with codecs.open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(self.__json_root, f, indent=2, sort_keys=True, ensure_ascii=False)

    class Accessor:
        def __init__(self, jr):
            self.__jr = jr
            self.__modified = False

        @property
        def modified(self):
            return self.__modified

        def __set_modified(self):
            self.__modified = True

        def __frames(self) -> dict[str, dict]:
            return self.__jr['frames']

        def list_labeled_frame_indexes(self) -> list[int]:
            return sorted(
                frame['fi']
                for frame in self.__frames().values()
            )

        def __frame(self, fi: int, create_if_absent=False) -> dict:
            frames = self.__frames()
            key = str(fi)
            if key not in frames:
                if not create_if_absent:
                    raise KeyError('key has not been created yet', key)
                else:
                    frames[key] = dict(
                        fi=fi,
                        label=None,
                        tags=[]
                    )
            return frames[key]

        def __remove_frame(self, fi: int):
            frames = self.__jr['frames']
            key = str(fi)
            if key in frames:
                del frames[key]
            self.__set_modified()

        def get_label(self, fi: int) -> Optional[str]:
            try:
                return self.__frame(fi)['label']
            except KeyError:
                return None

        def set_label(self, fi: int, label_name: str):
            self.remove_label(fi)
            self.__frame(fi, create_if_absent=True)['label'] = label_name
            self.__set_modified()

        def remove_label(self, fi: int):
            self.__remove_frame(fi)
            self.__set_modified()

        def get_tags(self, fi: int) -> tuple[str, ...]:
            try:
                return tuple(self.__frame(fi)['tags'])
            except KeyError:
                return tuple()

        def add_tag(self, fi: int, tag_name: str):
            if self.get_label(fi) is None:
                return
            tags = self.__frame(fi, create_if_absent=True)['tags']
            if tag_name in tags:
                return
            tags.append(tag_name)
            self.__set_modified()

        def remove_tag(self, fi: int, tag_name: str):
            try:
                self.__frame(fi)['tags'].remove(tag_name)
            except (KeyError, ValueError):
                pass
            finally:
                self.__set_modified()

        def get_label_count(self, fi: int) -> Optional[int]:
            target_label = self.get_label(fi)
            if target_label is None:
                return None

            # TODO: efficient algorithm
            count = 0
            for frame in self.__frames().values():
                label, i = frame['label'], frame['fi']
                if i > fi:
                    continue
                if label == target_label:
                    count += 1

            return count

        def find_nearest_labeled_index(
                self,
                fi_start: int,
                direction: int,
                n: int = None
        ) -> Union[list[int], Optional[int]]:
            assert direction in [+1, -1], direction

            fi_array = np.array(self.list_labeled_frame_indexes())

            if direction > 0:
                fi_array = np.sort(fi_array[fi_array > fi_start])
            else:
                fi_array = np.sort(fi_array[fi_array < fi_start])[::-1]

            if n is None:
                if len(fi_array) == 0:
                    return None
                return fi_array[0]
            else:
                return list(fi_array[:n])

    def __enter__(self):
        self.__lock.lock()
        self.__current_accessor = self.Accessor(self.__jr)
        return self.__current_accessor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self.__current_accessor.modified:
                print('DUMP!')
                self.dump()
        self.__lock.unlock()
        return False
