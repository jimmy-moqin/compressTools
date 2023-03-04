from PyQt5.QtWidgets import QApplication

from src.compressMain import CompressMain, DialogMain

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    Ui_CompressMain=CompressMain()
    Ui_CompressMain.show()#调用主窗口
    sys.exit(app.exec_())
