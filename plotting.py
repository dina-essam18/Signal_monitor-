from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtWidgets import QColorDialog
from PyQt5 import QtCore
from PyQt5.QtGui import QPixmap
import sys
import numpy as np
import pandas as pd
import statistics
from PyQt5.QtWidgets import QFileDialog, QGraphicsScene
from pyqtgraph import PlotWidget, PlotItem
import pyqtgraph as pg
import os
import img_rc
from scipy import signal
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
import pyqtgraph.exporters
from pathlib import Path


class SignalViewer(QtWidgets.QMainWindow):
    __added_sig_num = 0

    def __init__(self):
        super().__init__()
        uic.loadUi('GUI.ui', self)

        # creating timers
        self.timer1 = QtCore.QTimer()
        self.graphicsView_1.addLegend()

        # Connecting Buttons

        # File Menu
        self.actionAdd_Signals.triggered.connect(lambda: self.open_file())
        self.actionClearAll.triggered.connect(lambda: self.clear_all())
        self.actionExit.triggered.connect(lambda: self.exit())
        self.actionPrint_to_PDF.triggered.connect(lambda: self.export_pdf())

        # Color Menu
        self.actionPalette.triggered.connect(lambda: self.color())

        # Signal visibility
        self.show_signals.clicked.connect(lambda: self.show_signal())
        self.hide_signals.clicked.connect(lambda: self.hide())

        # Toolbar
        self.play_button.clicked.connect(lambda: self.play())
        self.stop_button.clicked.connect(lambda: self.stop())

        self.zoom_in.clicked.connect(lambda: self.zoomin())
        self.zoom_out.clicked.connect(lambda: self.zoomout())

        self.right_scroll.setMinimum(0)
        self.right_scroll.setMaximum(100)
        self.right_scroll.setValue(0)
        self.right_scroll.setTickInterval(15)
        self.right_scroll.valueChanged.connect(self.right)

        self.left_scroll.setMinimum(0)
        self.left_scroll.setMaximum(100)
        self.left_scroll.setValue(100)
        self.left_scroll.setTickInterval(1)
        self.left_scroll.valueChanged.connect(self.left)

        self.up_button.clicked.connect(lambda: self.up())
        self.down_button.clicked.connect(lambda: self.down())

        self.speed_signal.activated.connect(lambda: self.speed())

        # Signals Menu

        self.actionSignal_1.triggered.connect(
            lambda checked: (self.select_signal(1)))
        self.actionSignal_2.triggered.connect(
            lambda checked: (self.select_signal(2)))
        self.actionSignal_3.triggered.connect(
            lambda checked: (self.select_signal(3)))

        self.graphicsView_1.setXRange(min=0, max=10)
        self.pens = [pg.mkPen('r'), pg.mkPen('b'), pg.mkPen('g')]

        # Content for PDF

        self.fileName = 'Signal Report.pdf'
        self.documentTitle = 'Signals report'
        self.title = 'Signal Comparison'

        # Signals imgs used in generating PDF
        self.sig_img_1 = 'sig_img_1.png'
        self.sig_img_2 = 'sig_img_2.png'
        self.sig_img_3 = 'sig_img_3.png'
        self.spec_img_1 = 'spec_img_1.png'
        self.spec_img_2 = 'spec_img_2.png'
        self.spec_img_3 = 'spec_img_3.png'

        #  Create document with content given

        self.pdf = canvas.Canvas(self.fileName)
        self.pdf.setTitle(self.documentTitle)
        self.pdf.setPageSize((1800, 1000))
        #  Adjusting title

        self.pdf.setFont('Courier-Bold', 36)
        self.pdf.drawCentredString(850, 800, 'Signals Comparison')

        #  Adjusting sub-title

        self.pdf.setFont('Courier-Bold', 14)
        self.pdf.drawString(200, 665, 'Signal')
        self.pdf.drawString(430, 665, 'Spectrogram')
        self.pdf.drawString(660, 665, 'mean')
        self.pdf.drawString(890, 665, 'std')
        self.pdf.drawString(1100, 665, 'max')
        self.pdf.drawString(1350, 665, 'min')
        self.pdf.drawString(1580, 665, 'duration')

        #  Draw all lines for the table
        self.pdf.line(10, 650, 1800, 650)
        self.pdf.line(10, 450, 1800, 450)
        self.pdf.line(10, 250, 1800, 250)

        self.pdf.line(110, 50, 110, 700)
        self.pdf.line(350, 50, 350, 700)
        self.pdf.line(590, 50, 590, 700)

        self.pdf.line(830, 50, 830, 700)
        self.pdf.line(1070, 50, 1070, 700)
        self.pdf.line(1310, 50, 1310, 700)
        self.pdf.line(1550, 50, 1550, 700)

    # ###################################

    # Plotting the signals names
    def sigName(self, signal1, signal2, signal3):
        self.pdf.drawString(50, 550, signal1)
        self.pdf.drawString(50, 350, signal2)
        self.pdf.drawString(50, 150, signal3)

    # #Sending all signals images to their positions in the table
    def sigImage(self, img1, img2, img3):
        self.pdf.drawInlineImage(img1, 120, 465, width=190,
                                 height=170, preserveAspectRatio=False, showBoundary=True)
        self.pdf.drawInlineImage(img2, 120, 265, width=190,
                                 height=170, preserveAspectRatio=False, showBoundary=True)
        self.pdf.drawInlineImage(img3, 120, 65, width=190,
                                 height=170, preserveAspectRatio=False, showBoundary=True)

    # Sending all signals spectroimages to their positions in the table
    def spectroImage(self, img1, img2, img3):
        self.pdf.drawInlineImage(img1, 370, 465, width=190,
                                 height=170, preserveAspectRatio=False)
        self.pdf.drawInlineImage(img2, 370, 265, width=190,
                                 height=170, preserveAspectRatio=False)
        self.pdf.drawInlineImage(img3, 370, 65, width=190,
                                 height=170, preserveAspectRatio=False)

    def mean_data(self):
        self.mean1 = statistics.mean(self.amp1)
        self.mean2 = statistics.mean(self.amp2)
        self.mean3 = statistics.mean(self.amp3)
        return (self.mean1, self.mean2, self.mean3)

    def std_data(self):
        self.std1 = statistics.stdev(self.amp1)
        self.std2 = statistics.stdev(self.amp2)
        self.std3 = statistics.stdev(self.amp3)
        return (self.std1, self.std2, self.std3)

    def max_data(self):
        self.max1 = max(self.amp1)
        self.max2 = max(self.amp2)
        self.max3 = max(self.amp3)
        return (self.max1, self.max2, self.max3)

    def min_data(self):

        self.min1 = min(self.amp1)
        self.min2 = min(self.amp2)
        self.min3 = min(self.amp3)
        return (self.min1, self.min2, self.min3)

    def duration_date(self):
        self.duration1 = (self.time1[-1] - self.time1[0])
        self.duration2 = (self.time2[-1] - self.time2[0])
        self.duration3 = (self.time3[-1] - self.time3[0])
        return (self.duration1, self.duration2, self.duration3)

    def mean_signals(self):
        self.pdf.drawString(600, 465, str(statistics.mean(self.amp1)))
        self.pdf.drawString(600, 265, str(statistics.mean(self.amp2)))
        self.pdf.drawString(600, 65, str(statistics.mean(self.amp3)))

    def std_signals(self):
        self.pdf.drawString(850, 465, str(statistics.stdev(self.amp1)))
        self.pdf.drawString(850, 265, str(statistics.stdev(self.amp2)))
        self.pdf.drawString(850, 65, str(statistics.stdev(self.amp3)))

    def max_signals(self):
        self.pdf.drawString(1100, 465, str(max(self.amp1)))
        self.pdf.drawString(1100, 265, str(max(self.amp2)))
        self.pdf.drawString(1100, 65, str(max(self.amp3)))

    def min_signals(self):
        self.pdf.drawString(1350, 465, str(min(self.amp1)))
        self.pdf.drawString(1350, 265, str(min(self.amp2)))
        self.pdf.drawString(1350, 65, str(min(self.amp3)))

    def duration_signals(self):
        self.pdf.drawString(1600, 465, str((self.time1[-1] - self.time1[0])))
        self.pdf.drawString(1600, 265, str((self.time2[-1] - self.time2[0])))
        self.pdf.drawString(1600, 65, str((self.time3[-1] - self.time3[0])))

        # Which signal is controlled

    def select_signal(self, signal):
        if signal == 1:
            self.actionChannel_1.setChecked(True)


        elif signal == 2:
            self.actionChannel_1.setChecked(True)

        elif signal == 3:
            self.actionChannel_1.setChecked(True)

    def export_pdf(self):
        self.sigName('ECG', 'EOG', 'EMG')
        self.sigImage(self.sig_img_1, self.sig_img_2, self.sig_img_3)
        self.spectroImage(self.spec_img_1, self.spec_img_2, self.spec_img_3)
        self.mean_signals()
        self.std_signals()
        self.min_signals()
        self.max_signals()
        self.duration_signals()
        self.pdf.save()

    def get_extention(self, s):
        for i in range(1, len(s)):
            if s[-i] == '.':
                return s[-(i - 1):]

    # get signal name to show it as a title
    def get_sig_name(self, path):
        name = Path(path).name
        for i in range(1, len(name)):
            if path[-i] == '.':
                return name[:-(i)]

                # Clear all signals function

    def clear_all(self):
        self.__added_sig_num = 0
        self.graphicsView_1.clear()

    def open_file(self):
        self.__added_sig_num += 1
        self.fname1 = QtWidgets.QFileDialog.getOpenFileNames(
            self, 'Open only txt or CSV or xls', os.getenv('HOME'))

        # pass the elements of list in the tuple to the read_file function
        if self.__added_sig_num == 1:
            self.read_file1(self.fname1[0][0])
        if self.__added_sig_num == 2:
            self.read_file2(self.fname1[0][0])
        if self.__added_sig_num == 3:
            self.read_file3(self.fname1[0][0])

    def read_file1(self, file_path):
        path = file_path
        self.fileName1 = self.get_sig_name(path)
        self.file_ex = self.get_extention(path)
        if self.file_ex == 'txt':
            data1 = pd.read_csv(path)
            self.amp1 = data1.values[:, 0]
            self.time1 = np.linspace(0, 0.001 * len(self.amp1),
                                     len(self.amp1))  # generates time values corresponding to amplitudes in y
        if self.file_ex == 'csv':
            data1 = pd.read_csv(path)
            # contain the amplitudes
            self.amp1 = data1.values[:, 1]
            # containe the time values

            self.time1 = data1.values[0, 0]
        # plotting the signal 'static'
        self.data_line1 = self.graphicsView_1.plot(
            self.time1, self.amp1, name=self.fileName1, pen=self.pens[0])

        # #"Exporter" function is used to export the entire contents showed on "graphicsView" as an Image
        exporter = pg.exporters.ImageExporter(self.graphicsView_1.scene())
        exporter.export('sig_img_1.png')
        camp = plt.get_cmap('RdBu')
        plt.clf()
        plt.specgram(self.amp1, Fs=10e2, cmap=camp)
        plt.colorbar()

        # plt.specgram(self.amp1, Fs=10e2)  #specgram function takes the amplitude column and sampling frequency
        plt.xlabel('Time')
        plt.ylabel('Frequency')
        plt.savefig('spec_img_1.png', dpi=100, bbox_inches='tight')
        spectro_img = QPixmap('spec_img_1.png')
        self.spectrogram.setPixmap(spectro_img)
        plt.close()

    def update_plot_data1(self):
        time = self.time1[:self.idx1]
        amplitude = self.amp1[:self.idx1]
        self.idx1 += 50
        # shrink range of x-axis
        self.graphicsView_1.plotItem.setXRange(
            max(time, default=0) - 4, max(time, default=0))  ## -9
        # Plot the new data
        self.data_line1.setData(time, amplitude)

    def read_file2(self, file_path):
        path = file_path
        self.fileName2 = self.get_sig_name(path)
        self.file_ex = self.get_extention(path)
        if self.file_ex == 'txt':
            data2 = pd.read_csv(path)
            self.amp2 = data2.values[:, 0]
            self.time2 = np.linspace(0, 0.001 * len(self.amp2), len(self.amp2))
        if self.file_ex == 'csv':
            data2 = pd.read_csv(path)
            self.amp2 = data2.values[:, 1]
            self.time2 = data2.values[:, 0]
        self.data_line2 = self.graphicsView_1.plot(
            self.time2, self.amp2, name=self.fileName2, pen=self.pens[1])
        # #"Exporter" function is used to export the entire contents showed on "graphicsView" as an Image
        exporter = pg.exporters.ImageExporter(self.graphicsView_1.scene())
        exporter.export('sig_img_2.png')
        camp = plt.get_cmap('jet')
        plt.clf()
        plt.specgram(self.amp2, Fs=10e2, cmap=camp)
        plt.colorbar()

        # plt.specgram(self.amp1, Fs=10e2)  #specgram function takes the amplitude column and sampling frequency
        plt.xlabel('Time')
        plt.ylabel('Frequency')
        plt.savefig('spec_img_2.png', dpi=100, bbox_inches='tight')
        spectro_img = QPixmap('spec_img_2.png')
        self.spectrogram.setPixmap(spectro_img)
        plt.close()

        # #"Exporter" function is used to export the entire contents showed on "graphicsView" as an Image  
        # exporter = pg.exporters.ImageExporter(self.graphicsView_1.scene())
        # exporter.export('sig_img_2.png')

        # plt.specgram(self.amp2, Fs=10e2)
        # plt.xlabel('Time')
        # plt.ylabel('Frequency')

        # plt.savefig('spec_img_2.png', dpi=300, bbox_inches='tight')

    def update_plot_data2(self):
        time = self.time2[:self.idx2]
        amplitude = self.amp2[:self.idx2]
        self.idx2 += 50
        self.graphicsView_1.plotItem.setXRange(
            max(time, default=0) - 4, max(time, default=0))  # shrink range of x-axis  -18
        self.data_line2.setData(time, amplitude)

    def read_file3(self, file_path):
        path = file_path
        self.fileName3 = self.get_sig_name(path)
        self.file_ex = self.get_extention(path)
        if self.file_ex == 'txt':
            data3 = pd.read_csv(path)
            self.amp3 = data3.values[:, 0]
            self.time3 = np.linspace(0, 0.001 * len(self.amp3), len(self.amp3))
        if self.file_ex == 'csv':
            data3 = pd.read_csv(path)
            self.amp3 = data3.values[:, 1]
            self.time3 = data3.values[:, 0]
        self.data_line3 = self.graphicsView_1.plot(
            self.time3, self.amp3, name=self.fileName3, pen=self.pens[2])
        # #"Exporter" function is used to export the entire contents showed on "graphicsView" as an Image
        exporter = pg.exporters.ImageExporter(self.graphicsView_1.scene())
        exporter.export('sig_img_3.png')
        camp = plt.get_cmap('viridis')
        plt.clf()
        plt.specgram(self.amp3, Fs=10e2, cmap=camp)
        plt.colorbar()

        # plt.specgram(self.amp1, Fs=10e2)  #specgram function takes the amplitude column and sampling frequency
        plt.xlabel('Time')
        plt.ylabel('Frequency')
        plt.savefig('spec_img_3.png', dpi=100, bbox_inches='tight')
        spectro_img = QPixmap('spec_img_3.png')
        self.spectrogram.setPixmap(spectro_img)
        plt.close()

        # # "Exporter" function is used to export the entire contents showed on "graphicsView" as an Image  
        # exporter = pg.exporters.ImageExporter(self.graphicsView_1.scene())
        # exporter.export('sig_img_3.png')

        # plt.specgram(self.amp3, Fs=10e2)
        # plt.xlabel('Time')
        # plt.ylabel('Frequency')

        # plt.savefig('spec_img_3.png', dpi=300, bbox_inches='tight')

    def update_plot_data3(self):
        time = self.time3[:self.idx3]
        amplitude = self.amp3[:self.idx3]
        self.idx3 += 50
        self.graphicsView_1.plotItem.setXRange(
            max(time, default=0) - 4, max(time, default=0))
        self.data_line3.setData(time, amplitude)

    # Color function which set each signal color
    def color(self):
        palette = QColorDialog(self)
        palette.exec_()
        color = palette.selectedColor()

        if self.actionSignal_1.isChecked():
            self.graphicsView_1.plotItem.legend.removeItem(self.data_line1)
            self.data_line1 = self.graphicsView_1.plot(self.time1, self.amp1, name=self.fileName1, pen=pg.mkPen(color))

            return

        if self.actionSignal_2.isChecked():
            self.graphicsView_1.plotItem.legend.removeItem(self.data_line2)
            self.data_line2 = self.graphicsView_1.plot(self.time2, self.amp2, name=self.fileName2, pen=pg.mkPen(color))
            return

        if self.actionSignal_3.isChecked():
            self.graphicsView_1.plotItem.legend.removeItem(self.data_line3)
            self.data_line3 = self.graphicsView_1.plot(self.time3, self.amp3, name=self.fileName3, pen=pg.mkPen(color))
            return

    # Sending all signals spectroimages to their positions in the table
    def spectroImage(self, img1, img2, img3):
        self.pdf.drawInlineImage(img1, 370, 465, width=190,
                                 height=170, preserveAspectRatio=False)
        self.pdf.drawInlineImage(img2, 370, 265, width=190,
                                 height=170, preserveAspectRatio=False)
        self.pdf.drawInlineImage(img3, 370, 65, width=190,
                                 height=170, preserveAspectRatio=False)

    # Play function connected to play button
    def play(self):
        if self.actionSignal_1.isChecked():
            self.idx1 = 0
            self.timer1.setInterval(120)
            self.timer1.timeout.connect(self.update_plot_data1)
            self.timer1.start()

        if self.actionSignal_2.isChecked():
            self.idx2 = 0
            self.timer1.setInterval(120)
            self.timer1.timeout.connect(self.update_plot_data2)
            self.timer1.start()

        if self.actionSignal_3.isChecked():
            self.idx3 = 0
            self.timer1.setInterval(120)
            self.timer1.timeout.connect(self.update_plot_data3)
            self.timer1.start()

    # Stop function connected to Stop button
    def stop(self):
        if self.actionChannel_1.isChecked():
            self.timer1.stop()

    def speed(self):
        if self.speed_signal.currentIndex() == 1:
            self.timer1.setInterval(5)
        if self.speed_signal.currentIndex() == 2:
            self.timer1.setInterval(20)
        if self.speed_signal.currentIndex() == 3:
            self.timer1.setInterval(50)
        if self.speed_signal.currentIndex() == 4:
            self.timer1.setInterval(80)

    # Zoomin function connected to Zoomin button
    def zoomin(self):
        if self.actionChannel_1.isChecked():
            self.graphicsView_1.plotItem.getViewBox().scaleBy((0.5, 0.5))

    # Zoomout function connected to zoomout button
    def zoomout(self):
        if self.actionChannel_1.isChecked():
            self.graphicsView_1.plotItem.getViewBox().scaleBy((1.5, 1.5))

    def up(self):

        if self.actionSignal_1.isChecked():
            self.range = self.graphicsView_1.getViewBox().viewRange()
            if self.range[1][1] < max(self.amp1):
                self.graphicsView_1.getViewBox().translateBy(x=0, y=+0.2)
        if self.actionSignal_2.isChecked():
            self.range = self.graphicsView_1.getViewBox().viewRange()
            if self.range[1][1] < max(self.amp2):
                self.graphicsView_1.getViewBox().translateBy(x=0, y=+0.2)
        if self.actionSignal_3.isChecked():
            self.range = self.graphicsView_1.getViewBox().viewRange()
            if self.range[1][1] < max(self.amp3):
                self.graphicsView_1.getViewBox().translateBy(x=0, y=+0.2)

    def down(self):

        if self.actionSignal_1.isChecked():

            self.range = self.graphicsView_1.getViewBox().viewRange()
            if self.range[1][0] > min(self.amp1):
                self.graphicsView_1.getViewBox().translateBy(x=0, y=-0.2)
        if self.actionSignal_2.isChecked():
            self.range = self.graphicsView_1.getViewBox().viewRange()
            if self.range[1][0] > min(self.amp2):
                self.graphicsView_1.getViewBox().translateBy(x=0, y=-0.2)

        if self.actionSignal_3.isChecked():
            self.range = self.graphicsView_1.getViewBox().viewRange()
            if self.range[1][0] > min(self.amp3):
                self.graphicsView_1.getViewBox().translateBy(x=0, y=-0.2)



    def right(self):
        if self.right_scroll.value()>0:
            self.range = self.graphicsView_1.getViewBox().viewRange()
            # self.max_limit=max(self.x_limit)
            if self.range[0][1] < max(self.time1):
                self.graphicsView_1.getViewBox().translateBy(x=+0.2, y=0)

    def left(self):
        if self.right_scroll.value()>0:
            self.range = self.graphicsView_1.getViewBox().viewRange()
            if self.range[0][0] > min(self.time1):
                self.graphicsView_1.getViewBox().translateBy(x=-0.2, y=0)






    def hide(self):
        if self.actionSignal_1.isChecked():
            self.data_line1.hide()
        if self.actionSignal_2.isChecked():
            self.data_line2.hide()
        if self.actionSignal_3.isChecked():
            self.data_line3.hide()

    def show_signal(self):
        if self.actionSignal_1.isChecked():
            self.data_line1.show()
        if self.actionSignal_2.isChecked():
            self.data_line2.show()
        if self.actionSignal_3.isChecked():
            self.data_line3.show()




def main():
    app = QtWidgets.QApplication(sys.argv)
    application = SignalViewer()
    application.show()
    app.exec_()


if __name__ == "__main__":
    main()
