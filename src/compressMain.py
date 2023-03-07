import json
import os
import re
import subprocess
import time

from PyPDF2 import PdfFileReader
from PyQt5 import QtGui
from PyQt5.QtCore import QMutex, Qt, QThread, QUrl, QWaitCondition, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox, QWidget
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
        cmd = "gswin64c -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS={0} -dNOPAUSE -dBATCH -dDetectDuplicateImages -dCompressFonts=true  -sOutputFile={1} {2}".format(
            self.quality, self.savePath, self.pdfPath)

        ret = subprocess.Popen(
            cmd,
            shell=True,
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
                self.progressBarValue.emit(int(int(page) * 100 / int(self.pdfPages)))  # 发送进度条信号
                self.pages.emit(int(page))  # 发送页数信号
        self.signal_done.emit(1)  # 发送结束信号

    def stop(self):
        os.system("taskkill /pid %d -t -f" % self.pid)


class VideoPlayThread(QThread):
    tick = pyqtSignal(int)

    def __init__(self, videoPath, videoWidget):
        super(VideoPlayThread, self).__init__()
        self.videoPath = videoPath
        self.player = QMediaPlayer()
        self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.videoPath)))
        self.player.setVideoOutput(videoWidget)

        self.isPause = False
        self.isCancel = False
        self.cond = QWaitCondition()
        self.mutex = QMutex()

    def pause(self):
        self.isPause = True
        self.player.pause()

    def resume(self):
        self.isPause = False
        self.cond.wakeAll()
        self.player.play()

    def seek(self, position):
        self.player.setPosition(position)
        current_time = self.player.position()
        self.tick.emit(current_time)

    def stop(self):
        # 线程终止
        self.isCancel = True
        print("stop")

    def run(self):
        # 当视频在播放时
        while 1:
            self.mutex.lock()
            if self.isCancel:
                print("cancel")
                break
            elif self.isPause:
                self.cond.wait(self.mutex)
            elif self.player.state() == QMediaPlayer.PlayingState:
                # 获取当前播放的时间
                current_time = self.player.position()
                self.tick.emit(current_time)
                time.sleep(0.001)
            self.mutex.unlock()


class CompressVideoThread(QThread):
    progressBarValue = pyqtSignal(int)  # 更新进度条
    signal_done = pyqtSignal(int)  # 是否结束信号
    framesSignal = pyqtSignal(int)  # 帧数信号

    def __init__(self, videoCompressInfo):
        super(CompressVideoThread, self).__init__()
        self.isGPU = videoCompressInfo["isGPU"]
        self.savePath = videoCompressInfo["savePath"]
        self.videoPath = videoCompressInfo["videoPath"]
        self.audioBitRate = videoCompressInfo["audioBitRate"]
        self.videoResolution = videoCompressInfo["videoResolution"]
        self.videoFrameRate = videoCompressInfo["videoFrameRate"]
        self.frames = videoCompressInfo["frames"]
        self.startTick = str(videoCompressInfo["startTick"])
        self.endTick = str(videoCompressInfo["endTick"])

        self.isAuto = videoCompressInfo["isAuto"]
        
        if self.isAuto:
            self.limitSize = videoCompressInfo["limitSize"]
        else:
            self.videoBitRate = videoCompressInfo["videoBitRate"]
            self.videoType = videoCompressInfo["videoType"]
            

    def run(self):
        if self.isAuto:
            # 计算视频码率
            vbr = (int(self.limitSize) * 1024 * 8 / (int(self.endTick) - int(self.startTick))) - int(self.audioBitRate)
            if self.isGPU:
                cmd = [
                    "powershell.exe", 'ffmpeg', "-v", "quiet", "-stats", '-i', '\"' + self.videoPath + '\"', "-ss",
                    self.startTick, "-to", self.endTick, '-vcodec', 'h264_nvenc', "-b:v",
                    str(vbr)+"k","-s",self.videoResolution,"-r",str(self.videoFrameRate) ,"-y", '\"' + self.savePath + '\"', "2>&1 | ForEach-Object {$_ -replace '\\r', '\\n'}"
                ]
            else:
                cmd = [
                    "powershell.exe", 'ffmpeg', "-v", "quiet", "-stats", '-i', '\"' + self.videoPath + '\"', "-ss",
                    self.startTick, "-to", self.endTick,  "-b:v",
                    str(vbr)+"k","-s",self.videoResolution,"-r",str(self.videoFrameRate) ,"-y", '\"' + self.savePath + '\"', "2>&1 | ForEach-Object {$_ -replace '\\r', '\\n'}"
                ]
        else:
            if self.isGPU:
                cmd = [
                    "powershell.exe", 'ffmpeg', "-v", "quiet", "-stats", '-i', '\"' + self.videoPath + '\"', "-ss", self.startTick, "-to",
                    self.endTick, '-vcodec', 'h264_nvenc', '-s', self.videoResolution, '-r', self.videoFrameRate, '-b:v',
                    self.videoBitRate + "k", '-y', '\"' + self.savePath + '\"', "2>&1 | ForEach-Object {$_ -replace '\\r', '\\n'}"
                ]
            else:
                cmd = [
                    "powershell.exe", 'ffmpeg', "-v", "quiet", "-stats", '-i', '\"' + self.videoPath + '\"', "-ss", self.startTick, "-to",
                    self.endTick, '-s', self.videoResolution, '-r', self.videoFrameRate, '-b:v',
                    self.videoBitRate + "k", '-y', '\"' + self.savePath + '\"', "2>&1 | ForEach-Object {$_ -replace '\\r', '\\n'}"
                ]
        print(" ".join(cmd))
        ret = subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.pid = ret.pid
        # 获取处理到第几帧了
        while True:

            line = ret.stdout.readline()
            print(line)
            if not line:
                break
            if line.startswith(b"frame"):
                # 去除等号后面可能的空格
                line = re.sub(r"= +", "=", line.decode("utf-8"))
                frame = line.split()[0].replace("frame=", "")
                self.progressBarValue.emit(int(int(frame) * 100 / int(self.frames)))  # 发送进度条信号
                self.framesSignal.emit(int(frame))  # 发送帧数信号
        self.signal_done.emit(1)  # 发送结束信号

    def stop(self):
        os.system("taskkill /pid %d -t -f" % self.pid)


class DialogMain(QDialog, Ui_Dialog):

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
        self.tip.setText("处理完成!")
        self.pb.setValue(100)

    # 回传页数信号
    def flashPages(self, i):
        self.finishedPages.setText("已完成 {0} 页".format(i))

    def flashFrames(self, i):
        self.finishedPages.setText("已完成 {0} 帧".format(i))


class CompressMain(QWidget, Ui_CompressWidget):

    def __init__(self):
        super(CompressMain, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.initUI()

        self.dialog = DialogMain()

        # 设置usage按钮默认选中，以event的方式触发
        self.usageBtn.click()

    def initUI(self):
        self.isMaximized = False

        self.isUsageBtnChecked = False
        self.isPdfBtnChecked = False
        self.isVideoBtnChecked = False
        self.isSettingsBtnChecked = False
        self.isDonateBtnChecked = False

        self.isSelectPDF = False
        self.isSelectVideo = False

        self.isGPU = False

        self.leftIn = 0
        self.rightOut = self.playerSlider.maximum()

        # 设置GroupBox不可用
        if self.customizeRadioButton.isChecked():
            self.groupBox.setEnabled(True)
        else:
            self.groupBox.setEnabled(False)
        # 设置进度条不可用
        self.playerSlider.setEnabled(False)

        # 设置切片按钮不可用
        self.leftInBtn.setEnabled(False)
        self.rightOutBtn.setEnabled(False)

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

        # 绑定视频选择按钮事件
        self.videoBrowseBtn.clicked.connect(self.selectVideo)
        # 绑定清除选择按钮事件
        self.videoClearBtn.clicked.connect(self.clearVideo)
        # 绑定视频播放按钮事件
        self.stopBtn.clicked.connect(self.playEvent)

        # 绑定视频播放进度条事件
        self.playerSlider.sliderPressed.connect(self.sliderPressed)
        self.playerSlider.sliderReleased.connect(self.sliderReleased)

        # 绑定切入切出事件
        self.leftInBtn.clicked.connect(self.leftInEvent)
        self.rightOutBtn.clicked.connect(self.rightOutEvent)

        # 绑定视频压缩按钮事件
        self.runVideoCompressBtn.clicked.connect(self.runCompressVideo)

        # 绑定自动压制按钮事件
        self.autoRadioButton.clicked.connect(self.enableAuto)
        # 绑定自定义按钮事件
        self.customizeRadioButton.clicked.connect(self.enableGroupBox)

        # 绑定测试可用性按钮事件
        self.isAbleBtn.clicked.connect(self.testCUDA)

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

            self.pdfBtn.setStyleSheet("border-top-right-radius:15px;")
            self.isusageBtnChecked = True
        else:
            self.usageBtn.setStyleSheet("")
            self.isUsageBtnChecked = False
        self.setBtnEnabled()

        # 切换page
        self.stackedWidget.setCurrentIndex(0)

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

            self.usageBtn.setStyleSheet("border-bottom-right-radius:15px;")
            self.videoBtn.setStyleSheet("border-top-right-radius:15px;")
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

            self.pdfBtn.setStyleSheet("border-bottom-right-radius:15px;")
            self.settingsBtn.setStyleSheet("border-top-right-radius:15px;")
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

            self.videoBtn.setStyleSheet("border-bottom-right-radius:15px;")
            self.donateBtn.setStyleSheet("border-top-right-radius:15px;")
            self.isSettingsBtnChecked = True
        else:
            self.settingsBtn.setStyleSheet("")
            self.isSettingsBtnChecked = False
        self.setBtnEnabled()

        # 切换page
        self.stackedWidget.setCurrentIndex(3)

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

            self.settingsBtn.setStyleSheet("border-bottom-right-radius:15px;")
            self.isDonateBtnChecked = True
        else:
            self.donateBtn.setStyleSheet("")
            self.isDonateBtnChecked = False
        self.setBtnEnabled()

        # 切换page
        self.stackedWidget.setCurrentIndex(4)

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

    def selectVideo(self):
        # 选择视频文件
        videoPath, videoType = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", "Video Files (*.mp4 *.avi *.flv *.mkv *.mov *.wmv *.rmvb *.3gp *.webm)")
        if videoPath:
            # 尝试读取视频
            try:
                cmd = "ffprobe -v quiet -print_format json -show_format -show_streams \"{}\"".format(videoPath)
                self.videoInfo = json.loads(subprocess.check_output(cmd, shell=True))
                self.videoPath = videoPath
                self.videoPathLineEdit.setText(videoPath)
            except:
                QMessageBox.warning(self, "错误", "无法读取视频文件，请检查文件是否损坏")
                return

            # 设置文件信息
            # 先判断视频在第几轨道
            for i in range(len(self.videoInfo["streams"])):
                if self.videoInfo["streams"][i]["codec_type"] == "video":
                    videoTrack = i
                elif self.videoInfo["streams"][i]["codec_type"] == "audio":
                    audioTrack = i

            if len(os.path.basename(videoPath)) > 11:
                self.videoPathLabel.setText(os.path.basename(videoPath)[:11] + "...")
            else:
                self.videoPathLabel.setText(os.path.basename(videoPath))
            self.videoTypeLabel.setText(self.videoInfo["format"]["format_name"][:15])
            self.videoSizeLabel.setText(str(round(os.path.getsize(videoPath) / 1024 / 1024, 2)) + "MB")
            self.videoTimeLabel.setText("{:02d}:{:02d}:{:02d}".format(
                int(float(self.videoInfo["format"]["duration"]) / 3600),
                int(float(self.videoInfo["format"]["duration"]) / 60),
                int(float(self.videoInfo["format"]["duration"]) % 60)))
            self.videoResolutionLabel.setText("{}x{}".format(self.videoInfo["streams"][videoTrack]["width"],
                                                             self.videoInfo["streams"][videoTrack]["height"]))
            self.videoFrameLabel.setText(
                str(round(eval(self.videoInfo["streams"][videoTrack]["r_frame_rate"]), 2)) + "fps")
            self.videoBitLabel.setText("{}kbps".format(
                int(int(self.videoInfo["streams"][videoTrack]["bit_rate"]) / 1024)))
            self.audioBitLabel.setText("{}kbps".format(
                int(int(self.videoInfo["streams"][audioTrack]["bit_rate"]) / 1024)))
            self.audioChannelLabel.setText("{}".format(self.videoInfo["streams"][audioTrack]["channels"]))
            self.audioSampleLabel.setText("{}Hz".format(self.videoInfo["streams"][audioTrack]["sample_rate"]))

            # 设置剪辑信息初始值
            self.startTickLabel.setText("00:00:00")
            self.endTickLabel.setText(self.videoTimeLabel.text())
            self.durTimeLabel.setText(self.videoTimeLabel.text())

            self.startVideo()
        else:
            QMessageBox.warning(self, "错误", "请选择视频文件")

    def clearVideo(self):
        # 清除选择
        self.isSelectVideo = False
        self.videoPath = ""
        self.videoPathLineEdit.setText("")
        self.videoPathLabel.setText("")
        self.videoTypeLabel.setText("")
        self.videoSizeLabel.setText("")
        self.videoTimeLabel.setText("")
        self.videoResolutionLabel.setText("")
        self.videoFrameLabel.setText("")
        self.videoBitLabel.setText("")
        self.audioBitLabel.setText("")
        self.audioChannelLabel.setText("")
        self.audioSampleLabel.setText("")

    def startVideo(self):
        # 设置按钮可用
        self.leftInBtn.setEnabled(True)
        self.rightOutBtn.setEnabled(True)
        # 设置进度条归零,并设置最大值
        self.playerSlider.setEnabled(True)
        self.playerSlider.setValue(0)
        self.playerSlider.setMaximum(int(float(self.videoInfo["format"]["duration"]) * 1000))

        # # 设置时间初始化
        # self.tickLabel.setText("00:00:00.000")

        # 设置左右widget长度为0
        self.leftCutWidget.setFixedWidth(0)
        self.rightCutWidget.setFixedWidth(0)

        # 如果有视频播放线程,则停止
        if self.isSelectVideo:
            self.videoPlayThread.resume()
            self.videoPlayThread.stop()
            del self.videoPlayThread

        self.videoPlayThread = VideoPlayThread(self.videoPath, self.playerWidget)
        self.videoPlayThread.start()
        # 启动后视频暂停，线程立即挂起，否则会占用很多资源
        self.videoPlayThread.pause()
        self.stopBtn.setIcon(QIcon(":/basic/play.png"))
        self.isSelectVideo = True
        self.videoPlayThread.tick.connect(self.flashTime)

    def playEvent(self):
        if self.isSelectVideo:

            if self.videoPlayThread.player.state() == QMediaPlayer.PlayingState:
                self.videoPlayThread.pause()
                self.stopBtn.setIcon(QIcon(":/basic/play.png"))
            else:
                self.videoPlayThread.resume()
                self.stopBtn.setIcon(QIcon(":/basic/pause.png"))
        else:
            QMessageBox.warning(self, "错误", "请选择视频文件")

    def flashTime(self, i):
        # 刷新时间
        self.playerSlider.setValue(i)
        h = int(i / 3600000)
        m = int((i - h * 3600000) / 60000)
        s = int((i - h * 3600000 - m * 60000) / 1000)
        ms = int(i - h * 3600000 - m * 60000 - s * 1000)
        self.tickLabel.setText("{:02d}:{:02d}:{:02d}.{:03d}".format(h, m, s, ms))

    def sliderReleased(self):
        tick = self.playerSlider.value()
        self.videoPlayThread.seek(tick)
        self.playerSlider.setValue(tick)
        self.flashTime(tick)

    def sliderPressed(self):
        self.videoPlayThread.pause()
        self.stopBtn.setIcon(QIcon(":/basic/play.png"))

    def leftInEvent(self):
        # 左边进
        self.videoPlayThread.pause()
        self.stopBtn.setIcon(QIcon(":/basic/play.png"))

        if self.playerSlider.value() > self.rightOut:
            self.rightOut = self.playerSlider.maximum()
            self.rightCutWidget.setMinimumWidth(0)
        else:
            pass
        self.leftIn = self.playerSlider.value()
        # 获取进度条的实际长度
        sliderWidth = self.playerSlider.width()
        # 获取进度条的最大值
        sliderMax = self.playerSlider.maximum()
        # 计算比率
        ratioWidth = (self.leftIn / sliderMax) * sliderWidth
        # 设置左侧弹簧长度
        self.leftCutWidget.setMinimumWidth(ratioWidth)

        # 记录左边进的时间
        self.startTickLabel.setText(self.getTick(self.leftIn))
        self.getDuration()

    def rightOutEvent(self):
        # 右边出
        self.videoPlayThread.pause()
        self.stopBtn.setIcon(QIcon(":/basic/play.png"))

        if self.playerSlider.value() < self.leftIn:
            self.leftIn = 0
            self.leftCutWidget.setMinimumWidth(0)
        else:
            pass
        self.rightOut = self.playerSlider.value()
        # 获取进度条的实际长度
        sliderWidth = self.playerSlider.width()
        # 获取进度条的最大值
        sliderMax = self.playerSlider.maximum()
        # 计算比率
        ratioWidth = ((sliderMax - self.rightOut) / sliderMax) * sliderWidth
        # 设置右侧弹簧长度
        self.rightCutWidget.setMinimumWidth(ratioWidth)

        # 记录右边出的时间
        self.endTickLabel.setText(self.getTick(self.rightOut))
        self.getDuration()

    def getTick(self, position):
        # 获取时间
        h = int(position / 3600000)
        m = int((position - h * 3600000) / 60000)
        s = int((position - h * 3600000 - m * 60000) / 1000)
        return "{:02d}:{:02d}:{:02d}".format(h, m, s)

    def getSec(self, tick):
        # 获取秒数
        h, m, s = tick.split(":")
        return int(h) * 3600 + int(m) * 60 + int(s)

    def getDuration(self):
        # 计算剪辑的起止时间差
        start = self.leftIn
        end = self.rightOut
        h = int((end - start) / 3600000)
        m = int(((end - start) - h * 3600000) / 60000)
        s = int(((end - start) - h * 3600000 - m * 60000) / 1000)
        self.durTimeLabel.setText("{:02d}:{:02d}:{:02d}".format(h, m, s))

    def runCompressVideo(self):
        # 开始压制
        # 获取保存路径
        savePath = QFileDialog.getSaveFileName(self, "保存视频", "", "MP4(*.mp4)")[0]
        if savePath:
            # 获取压制信息
            self.vInfo = {}
            if self.isGPU:
                self.vInfo["isGPU"] = True
            else:
                self.vInfo["isGPU"] = False
            if self.autoRadioButton.isChecked():
                self.vInfo["isAuto"] = True
                self.vInfo["savePath"] = savePath
                self.vInfo["videoPath"] = self.videoPathLineEdit.text()
                self.vInfo["limitSize"] = str(int(self.limitSizeLineEdit.text()) - 5)
                self.vInfo["videoResolution"] = self.videoDefaultResolutionComboBox.currentText()
                self.vInfo["videoFrameRate"] = self.videoDefaultFrameRateLineEdit.text()
                self.vInfo["audioBitRate"] = self.audioBitLabel.text().replace("kbps", "")
                self.vInfo["frames"] = int(
                    (self.getSec(self.endTickLabel.text()) - self.getSec(self.startTickLabel.text())) * 20)
                self.vInfo["startTick"] = self.getSec(self.startTickLabel.text())
                self.vInfo["endTick"] = self.getSec(self.endTickLabel.text())
            elif self.customizeRadioButton.isChecked():
                self.vInfo["isAuto"] = False
                self.vInfo["savePath"] = savePath
                self.vInfo["videoPath"] = self.videoPathLineEdit.text()
                self.vInfo["videoType"] = self.vTypeComboBox.currentText()
                self.vInfo["videoResolution"] = self.vResolutionComboBox.currentText()
                self.vInfo["videoFrameRate"] = self.vFrameComboBox.currentText().replace("fps", "")
                self.vInfo["videoBitRate"] = self.vBitLineEdit.text()
                self.vInfo["audioBitRate"] = self.audioBitLabel.text().replace("kbps", "")
                self.vInfo["frames"] = int(
                    (self.getSec(self.endTickLabel.text()) - self.getSec(self.startTickLabel.text())) *
                    float(self.vFrameComboBox.currentText().replace("fps", "")))
                self.vInfo["startTick"] = self.getSec(self.startTickLabel.text())
                self.vInfo["endTick"] = self.getSec(self.endTickLabel.text())

            # 弹出对话框
            self.dialog.setWindowModality(Qt.ApplicationModal)
            self.dialog.tip.setText("正在压制视频,请稍后...")
            self.dialog.finishedPages.setText("已完成 {} 帧".format(0))
            self.dialog.totalPages.setText("共约 {} 帧".format(self.vInfo["frames"]))
            self.dialog.pb.setValue(0)
            self.dialog.show()

            # 开始压制
            self.cvThread = CompressVideoThread(self.vInfo)
            self.cvThread.start()
            self.cvThread.progressBarValue.connect(self.dialog.callback)
            self.cvThread.framesSignal.connect(self.dialog.flashFrames)
            self.cvThread.signal_done.connect(self.dialog.callback_done)
            # 如果点击Cancel,则停止压缩
            self.dialog.cancelBtn.clicked.connect(self.cvThread.stop)
        else:
            QMessageBox.warning(self, "错误", "请选择保存路径")
            return

    def enableGroupBox(self):
        if self.customizeRadioButton.isChecked():
            self.groupBox.setEnabled(True)

    def enableAuto(self):
        if self.autoRadioButton.isChecked():
            self.groupBox.setEnabled(False)

    def testCUDA(self):
        # 测试CUDA是否可用
        if self.hwComboBox.currentText() == "CPU":
            self.isGPU = False
        else:
            cmd = "nvidia-smi"
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if err:
                print(err)
                QMessageBox.warning(self, "错误", "CUDA不可用,请检查CUDA是否安装")
                return False
            else:
                cmd = "ffmpeg -v quiet -hwaccels"
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                if out:
                    hwList = out.decode("utf-8").split("\r\n")
                    for hw in hwList:
                        if hw == "cuda":
                            self.isGPU = True
                            QMessageBox.information(self, "提示", "CUDA可用")
                            break
                    else:
                        self.isGPU = False
                        QMessageBox.warning(self, "错误", "CUDA不可用,请检查CUDA是否安装")


