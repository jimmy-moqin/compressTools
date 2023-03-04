
import os
import subprocess
import time

from PyPDF2 import PdfFileReader
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog,
                             QHeaderView, QItemDelegate, QMessageBox,
                             QTableWidgetItem, QWidget)
from ui.compress import Ui_CompressWidget
from ui.dialog import Ui_Dialog


class CompressThread(QThread):
    progressBarValue = pyqtSignal(int)  # 更新进度条
    signal_done = pyqtSignal(int)  # 是否结束信号
    pages = pyqtSignal(int)  # 页数信号

    def __init__(self, compressInfo):
        super(CompressThread, self).__init__()
        self.pdfPath = compressInfo["pdfPath"]
        self.savePath = compressInfo["savePath"]
        self.pdfPages = compressInfo["pdfPages"]
        self.quality = compressInfo["quality"]

    def run(self):
        cmd = "gswin64c -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS={0} -dNOPAUSE -dBATCH -dDetectDuplicateImages -dCompressFonts=true  -sOutputFile={1} {2}".format(self.quality, self.savePath, self.pdfPath)
        
        ret = subprocess.Popen(cmd,shell=True,
                 stdin=subprocess.PIPE,
                 stdout=subprocess.PIPE,
                 stderr=subprocess.PIPE,
                 )
        self.pid = ret.pid
        # 获取压缩到第几页了
        while True:
            line = ret.stdout.readline()
            if not line:
                break
            if line.startswith(b"Page"):
                page = line.split()[1]
                self.progressBarValue.emit(int(int(page)*100/int(self.pdfPages)))  # 发送进度条信号 
                self.pages.emit(int(page))  # 发送页数信号
        self.signal_done.emit(1)  # 发送结束信号

    def stop(self):
        os.system("taskkill /pid %d -t -f" % self.pid)



class DialogMain(QDialog,Ui_Dialog):
    def __init__(self):
        super(DialogMain, self).__init__()
        self.setupUi(self)
        # self.setWindowFlags(
        #     Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.initUI()

    def initUI(self):
        # 设置ok按钮不可用
        self.okBtn.setEnabled(False)

        # 绑定ok按钮事件
        self.okBtn.clicked.connect(self.close)
        # 绑定取消按钮事件
        self.cancelBtn.clicked.connect(self.close)


    # 回传进度条参数
    def callback(self, i):
        self.pb.setValue(i)
    
    # 回传结束信号
    def callback_done(self, i):
        self.okBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)
        self.tip.setText("压缩完成!")
        self.pb.setValue(100)

    # 回传页数信号
    def flashPages(self, i):
        self.finishedPages.setText("已完成 {0} 页".format(i))

class CompressMain(QWidget, Ui_CompressWidget):

    def __init__(self):
        super(CompressMain, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.initUI()

        self.dialog = DialogMain()
    
    def initUI(self):
        self.isMaximized = False

        self.isUsageBtnChecked = False
        self.isPdfBtnChecked = False
        self.isVideoBtnChecked = False
        self.isSettingsBtnChecked = False
        self.isDonateBtnChecked = False

        self.isSelectPDF = False

        # 绑定窗口变化按钮事件
        self.minBtn.clicked.connect(self.minEvent)
        self.maxBtn.clicked.connect(self.maxEvent)
        self.closeBtn.clicked.connect(self.closeEvent)

        # 绑定分页按钮事件
        self.usageBtn.clicked.connect(self.usageBtnEvent)
        self.pdfBtn.clicked.connect(self.pdfBtnEvent)
        self.videoBtn.clicked.connect(self.videoBtnEvent)
        self.settingsBtn.clicked.connect(self.settingsBtnEvent)
        self.donateBtn.clicked.connect(self.donateBtnEvent)

        # 绑定PDF文件选择按钮事件
        self.pdfBrowseBtn.clicked.connect(self.selectPDF)
        # 绑定清除选择按钮事件
        self.pdfClearBtn.clicked.connect(self.clearPDF)
        # 绑定压缩按钮事件
        self.runCompressBtn.clicked.connect(self.compressPDF)
    
    def closeEvent(self, event):
        # 重写关闭事件
        self.close()
    def minEvent(self, event):
        # 重写最小化事件
        self.showMinimized()
    def maxEvent(self, event):
        # 重写最大化事件
        if self.isMaximized:
            # change icon
            self.maxBtn.setIcon(QtGui.QIcon(":/basic/max.png"))
            self.showNormal()
            self.isMaximized = False
        else:
            # change icon
            self.maxBtn.setIcon(QtGui.QIcon(":/basic/shrink.png"))
            self.showMaximized()
            self.isMaximized = True

    def usageBtnEvent(self, event):
        # 重写使用说明事件
        if not self.isUsageBtnChecked:
            # 清除其他按钮的点击状态
            self.pdfBtn.setChecked(False)
            self.videoBtn.setChecked(False)
            self.settingsBtn.setChecked(False)
            self.donateBtn.setChecked(False)
            self.isPdfBtnChecked = False
            self.isVideoBtnChecked = False
            self.isSettingsBtnChecked = False
            self.isDonateBtnChecked = False

            # 清除其他按钮的样式
            self.pdfBtn.setStyleSheet("")
            self.videoBtn.setStyleSheet("")
            self.settingsBtn.setStyleSheet("")
            self.donateBtn.setStyleSheet("")

            self.pdfBtn.setStyleSheet(
                "border-top-right-radius:15px;"
            )
            self.isusageBtnChecked = True
        else:
            self.usageBtn.setStyleSheet("")
            self.isUsageBtnChecked = False
        self.setBtnEnabled()
    
    def pdfBtnEvent(self, event):
        # 重写pdf事件     
        if not self.isPdfBtnChecked:
            
            # 清除其他按钮的点击状态
            self.usageBtn.setChecked(False)
            self.videoBtn.setChecked(False)
            self.settingsBtn.setChecked(False)
            self.donateBtn.setChecked(False)
            self.isUsageBtnChecked = False
            self.isVideoBtnChecked = False
            self.isSettingsBtnChecked = False
            self.isDonateBtnChecked = False

            # 清除其他按钮的样式
            self.usageBtn.setStyleSheet("")
            self.videoBtn.setStyleSheet("")
            self.settingsBtn.setStyleSheet("")
            self.donateBtn.setStyleSheet("")

            self.usageBtn.setStyleSheet(
                "border-bottom-right-radius:15px;"
            )
            self.videoBtn.setStyleSheet(
                "border-top-right-radius:15px;"
            )
            self.isPdfBtnChecked = True
        else:
            self.pdfBtn.setStyleSheet("")
            self.isPdfBtnChecked = False
        self.setBtnEnabled()

        # 切换page
        self.stackedWidget.setCurrentIndex(1)
    
    def videoBtnEvent(self, event):
        # 重写视频事件
        if not self.isVideoBtnChecked:
            # 清除其他按钮的点击状态
            self.usageBtn.setChecked(False)
            self.pdfBtn.setChecked(False)
            self.settingsBtn.setChecked(False)
            self.donateBtn.setChecked(False)
            self.isUsageBtnChecked = False
            self.isPdfBtnChecked = False
            self.isSettingsBtnChecked = False
            self.isDonateBtnChecked = False

            # 清除其他按钮的样式
            self.usageBtn.setStyleSheet("")
            self.pdfBtn.setStyleSheet("")
            self.settingsBtn.setStyleSheet("")
            self.donateBtn.setStyleSheet("")

            self.pdfBtn.setStyleSheet(
                "border-bottom-right-radius:15px;"
            )
            self.settingsBtn.setStyleSheet(
                "border-top-right-radius:15px;"
            )
            self.isVideoBtnChecked = True
        else:
            self.videoBtn.setStyleSheet("")
            self.isVideoBtnChecked = False
        self.setBtnEnabled()

        # 切换page
        self.stackedWidget.setCurrentIndex(2)

    def settingsBtnEvent(self, event):
        # 重写设置事件
        if not self.isSettingsBtnChecked:
            # 清除其他按钮的点击状态
            self.usageBtn.setChecked(False)
            self.pdfBtn.setChecked(False)
            self.videoBtn.setChecked(False)
            self.donateBtn.setChecked(False)
            self.isUsageBtnChecked = False
            self.isPdfBtnChecked = False
            self.isVideoBtnChecked = False
            self.isDonateBtnChecked = False

            # 清除其他按钮的样式
            self.usageBtn.setStyleSheet("")
            self.pdfBtn.setStyleSheet("")
            self.videoBtn.setStyleSheet("")
            self.donateBtn.setStyleSheet("")

            self.videoBtn.setStyleSheet(
                "border-bottom-right-radius:15px;"
            )
            self.donateBtn.setStyleSheet(
                "border-top-right-radius:15px;"
            )
            self.isSettingsBtnChecked = True
        else:
            self.settingsBtn.setStyleSheet("")
            self.isSettingsBtnChecked = False
        self.setBtnEnabled()
    
    def donateBtnEvent(self, event):
        # 重写捐赠事件
        if not self.isDonateBtnChecked:
            # 清除其他按钮的点击状态
            self.usageBtn.setChecked(False)
            self.pdfBtn.setChecked(False)
            self.videoBtn.setChecked(False)
            self.settingsBtn.setChecked(False)
            self.isUsageBtnChecked = False
            self.isPdfBtnChecked = False
            self.isVideoBtnChecked = False
            self.isSettingsBtnChecked = False

            # 清除其他按钮的样式
            self.usageBtn.setStyleSheet("")
            self.pdfBtn.setStyleSheet("")
            self.videoBtn.setStyleSheet("")
            self.settingsBtn.setStyleSheet("")

            self.settingsBtn.setStyleSheet(
                "border-bottom-right-radius:15px;"
            )
            self.isDonateBtnChecked = True
        else:
            self.donateBtn.setStyleSheet("")
            self.isDonateBtnChecked = False
        self.setBtnEnabled()

    def setBtnEnabled(self):
        for btn in [self.usageBtn, self.pdfBtn, self.videoBtn, self.settingsBtn, self.donateBtn]:
            if btn.isChecked():
                btn.setEnabled(False)
            else:
                btn.setEnabled(True)
    
    def selectPDF(self):
        # 选择PDF文件
        pdfPath, pdfType = QFileDialog.getOpenFileName(self, "选择PDF文件", "", "PDF Files (*.pdf)")
        if pdfPath:
            self.pdfPath = pdfPath
            self.pdfSelectLineEdit.setText(pdfPath)
            # 尝试读取pdf
            try:
                self.pdf = PdfFileReader(pdfPath)
            except:
                QMessageBox.warning(self, "错误", "无法读取PDF文件，请检查文件是否损坏")
                self.isSelectPDF = False
                return
            # 设置文件信息
            self.fileNameLabel.setText(os.path.basename(pdfPath))
            self.fileTypeLabel.setText("PDF")
            self.fileSizeLabel.setText(str(round(os.path.getsize(pdfPath) / 1024 / 1024, 2)) + "MB")
            self.filePagesLabel.setText(str(self.pdf.getNumPages()))
            self.createTimeLabel.setText(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(pdfPath))))
            self.modifyTimeLabel.setText(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(pdfPath))))

            self.isSelectPDF = True

        else:
            QMessageBox.warning(self, "错误", "请选择PDF文件")
    
    def clearPDF(self):
        # 清除选择
        self.isSelectPDF = False
        self.pdfPath = ""
        self.pdfSelectLineEdit.setText("")
        self.fileNameLabel.setText("")
        self.fileTypeLabel.setText("")
        self.fileSizeLabel.setText("")
        self.filePagesLabel.setText("")
        self.createTimeLabel.setText("")
        self.modifyTimeLabel.setText("")

    def compressPDF(self):
        if self.lowRadioButton.isChecked():
            quality = "/screen"
        elif self.midRadioButton.isChecked():
            quality = "/ebook"
        elif self.highRadioButton.isChecked():
            quality = "/printer"
        else:
            QMessageBox.warning(self, "错误", "请选择压缩质量")
            return

        if self.isSelectPDF:
            # 选择保存路径
            savePath, saveType = QFileDialog.getSaveFileName(self, "保存PDF文件", "保存", "PDF Files (*.pdf)")
            if savePath:
                # 弹出Dialog,同时锁定主窗口
                self.dialog.setWindowModality(Qt.ApplicationModal) 
                
                # 设置总页数
                self.dialog.totalPages.setText("共 {} 页".format(self.filePagesLabel.text()))
                # 设置进度条归零
                self.dialog.pb.setValue(0)
                # 设置tip
                self.dialog.tip.setText("正在压缩，请稍后...")
                # 设置已完成页数归零
                self.dialog.finishedPages.setText("已完成 0 页")
                # 设置取消按钮可用
                self.dialog.cancelBtn.setEnabled(True)
                # 设置完成按钮不可用
                self.dialog.okBtn.setEnabled(False)
                
                # 显示Dialog
                self.dialog.show()
                # 开始压缩
                compressInfo = {
                    "pdfPath": self.pdfPath,
                    "savePath": savePath,
                    "quality": quality,
                    "pdfPages": self.filePagesLabel.text()
                }
                self.compress_thread = CompressThread(compressInfo)
                # 连接信号到进度条
                self.compress_thread.progressBarValue.connect(self.dialog.callback)
                # 连接信号到进度条文本
                self.compress_thread.pages.connect(self.dialog.flashPages)

                # 连接信号到完成
                self.compress_thread.signal_done.connect(self.dialog.callback_done)
                self.compress_thread.start()

                # 如果点击Cancel,则停止压缩
                self.dialog.cancelBtn.clicked.connect(self.compress_thread.stop)
            else:
                QMessageBox.warning(self, "错误", "请选择保存路径")
                return
        else:
            QMessageBox.warning(self, "错误", "请选择PDF文件")
            return


