
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QFileDialog, QHeaderView, QItemDelegate,
                             QMessageBox, QTableWidgetItem, QWidget)
from ui.compress import Ui_CompressWidget


class CompressMain(QWidget, Ui_CompressWidget):

    def __init__(self):
        super(CompressMain, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.initUI()
    
    def initUI(self):
        self.isMaximized = False

        self.isUsageBtnChecked = False
        self.isPdfBtnChecked = False
        self.isVideoBtnChecked = False
        self.isSettingsBtnChecked = False
        self.isDonateBtnChecked = False

        self.minBtn.clicked.connect(self.minEvent)
        self.maxBtn.clicked.connect(self.maxEvent)
        self.closeBtn.clicked.connect(self.closeEvent)

        self.usageBtn.clicked.connect(self.usageBtnEvent)
        self.pdfBtn.clicked.connect(self.pdfBtnEvent)
        self.videoBtn.clicked.connect(self.videoBtnEvent)
        self.settingsBtn.clicked.connect(self.settingsBtnEvent)
        self.donateBtn.clicked.connect(self.donateBtnEvent)
    
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
                