import os
from enum import Enum

_FILE_ABSOLUTE = os.path.abspath(__file__)
_SOURCES_ROOT = os.path.dirname(_FILE_ABSOLUTE)
_PROJECT_ROOT = os.path.dirname(_SOURCES_ROOT)

assert 'run.bat' in os.listdir(_PROJECT_ROOT), _PROJECT_ROOT

print(f'{_PROJECT_ROOT=}')


class Domain(Enum):
    RESOURCES = 'resources'
    MARKDATA = 'markdata'
    APPINFO = 'appinfo'
    TEMPLATE = 'label-template'

    def __init__(self, dir_name):
        self.__dir_name = dir_name

    @property
    def dir_name(self):
        return self.__dir_name


def resolve(domain: Domain, *args) -> str:
    path = os.path.join(
        _PROJECT_ROOT,
        domain.dir_name,
        *args
    )
    path = os.path.normpath(path)
    path = os.path.abspath(path)
    return path
