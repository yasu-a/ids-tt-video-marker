import sys
import traceback

from PyQt5.QtWidgets import *

from main import MainWindow


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(tb, file=sys.stderr)
    QApplication.quit()
    # or QtWidgets.QApplication.exit(0)


sys.excepthook = excepthook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("*{font-size: 11pt; font-family: Consolas;}")
    ew = MainWindow()
    ew.show()
    sys.exit(app.exec_())
