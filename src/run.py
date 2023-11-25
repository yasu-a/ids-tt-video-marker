import codecs
import datetime
import os
import re
import sys
import traceback
from pprint import pformat

from PyQt5.QtWidgets import *

from common import DEBUG
from main import MainWindow
from res import resolve, Domain


def get_sys_info():
    import platform
    import socket
    info = {
        'version': sys.version_info,
        'platform': platform.system(),
        'platform-release': platform.release(),
        'platform-version': platform.version(),
        'architecture': platform.machine(),
        'hostname': socket.gethostname(),
        'processor': platform.processor()
    }
    info = {k: str(v) for k, v in info.items()}
    return info


def excepthook(exc_type, exc_value, exc_tb):
    tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb, file=sys.stderr)

    if not DEBUG:
        str_now = re.sub(r'[^0-9a-zA-Z]', '_', str(datetime.datetime.now())[:-7])
        dump_path = resolve(
            Domain.ERRORS,
            'log_' + str_now + '.txt'
        )
        dump_path = os.path.normpath(dump_path)
        dump_path = os.path.abspath(dump_path)

        text = [
            'エラーが発生しました。',
            '以下のファイルに出力されたエラーの内容とともに製作者に連絡してください。',
            dump_path,
            '',
            *tb.split('\n'),
            *pformat(get_sys_info()).split('\n')
        ]
        text = '\n'.join(text)
        print(text, file=sys.stderr)

        os.makedirs(os.path.dirname(dump_path), exist_ok=True)
        with codecs.open(dump_path, 'w', 'utf-8') as f:
            f.write(text)

    app.exit(-1)


sys.excepthook = excepthook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    if os.name == 'nt':
        app.setStyleSheet("*{font-size: 11pt; font-family: Consolas;}")
    else:
        app.setStyleSheet("*{font-size: 11pt; font-family: Courier;}")
    ew = MainWindow()
    ew.show()
    sys.exit(app.exec_())
