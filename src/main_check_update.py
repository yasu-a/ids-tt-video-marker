import os
import sys
import traceback
import webbrowser

from PyQt5.QtWidgets import *

import version


def excepthook(exc_type, exc_value, exc_tb):
    tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb, file=sys.stderr)
    app.exit(-1)


sys.excepthook = excepthook


class MainWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.__init_ui()
        self.__url = None

        self.show_update()

    def __init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        button = QPushButton(self)
        # noinspection PyUnresolvedReferences
        button.clicked.connect(self.button_clicked)
        layout.addWidget(button)
        self.button = button

    def show_update(self):
        version_name = version.app_version_str
        if version.update_available:
            url = version.latest_version_info['url']
            print(url)
            self.__url = url
            text = f'アップデートが利用可能です（現在のバージョン: {version_name}）'
            self.button.setEnabled(True)
        else:
            text = f'最新バージョンです: {version_name}'
            self.button.setEnabled(False)
        self.button.setText(text)

    def button_clicked(self):
        webbrowser.open(self.__url)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if os.name == 'nt':
        app.setStyleSheet("*{font-size: 11pt; font-family: Consolas;}")
    else:
        app.setStyleSheet("*{font-size: 11pt; font-family: Courier;}")
    ew = MainWidget()
    # noinspection PyUnresolvedReferences
    ew.show()
    sys.exit(app.exec_())
