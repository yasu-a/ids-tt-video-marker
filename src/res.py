import os
from enum import Enum
from typing import Literal

_FILE_ABSOLUTE = os.path.abspath(__file__)
_SOURCES_ROOT = os.path.dirname(_FILE_ABSOLUTE)
_PROJECT_ROOT = os.path.dirname(_SOURCES_ROOT)

assert 'run.bat' in os.listdir(_PROJECT_ROOT), _PROJECT_ROOT

print(f'{_PROJECT_ROOT=}')


class Domain(Enum):
    ERRORS = 'error-logs'
    RESOURCES = 'resources'
    MARKDATA = 'markdata'
    MARKDATA_BACKUP = 'markdata-backup'
    APPINFO = 'appinfo'
    TEMPLATE = 'label-template'

    def __init__(self, dir_name):
        self.__dir_name = dir_name

    @property
    def dir_name(self):
        return self.__dir_name


def resolve(domain: Domain, *args, make_dirs: Literal['parent', 'self'] = None) -> str:
    path = os.path.join(
        _PROJECT_ROOT,
        domain.dir_name,
        *args
    )
    path = os.path.normpath(path)
    path = os.path.abspath(path)

    if make_dirs is not None:
        if make_dirs == 'parent':
            os.makedirs(os.path.dirname(path), exist_ok=True)
        elif make_dirs == 'self':
            os.makedirs(path, exist_ok=True)
        else:
            assert False, make_dirs

    return path
