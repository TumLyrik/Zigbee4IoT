# GUI
from PyQt5.QtWidgets import*
from PyQt5.uic import loadUi
from PyQt5 import QtGui
from numpy import double
import pyqtgraph as pg
#from datetime import datetime
import re
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import (Qt, QTimer, QPointF, QIODevice, pyqtSlot)

#from random import randint

STR_COM = 'ttyUSB0'
NODE_NUM = 8
REFRESH_TIME_MS = 100
dataRxList= []
dataTHList= [0.00,0.00]
dataVList= [0,0,0]
dataTxList= []
#timelist= []

class sensorBoxUI(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi("SensorboxV1.ui",self)
        self.initUI()
        self.initPlot()
        self.ORun.clicked.connect(self.runBox)
        self.OStop.clicked.connect(self.stopBox)
        self.OPower.clicked.connect(self.powerBox)
        
    def initUI(self):
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        self.comboBox.addItem('SensorBox001')
    
    def messageW(self,mess):
        if self.listWidget.count() >= 11:
            self.listWidget.clear()
        self.listWidget.addItem(mess)

    def initPlot(self):
        p1= self.OTH
        p1.setYRange(0,50)
        p1.addLegend()
        p1.showGrid(x=False, y=True, alpha=0.8)
        penGy= pg.mkColor(240,240,240)
        p1.setBackground(penGy)
        ### data
        p1.x, p1.t, p1.h, p1.dSize= [], [], [], 0
        p1.tLine= p1.plot(p1.x,p1.t,pen='g')
        p1.hLine= p1.plot(p1.x,p1.h,pen='r')
        p1.getPlotItem().hideAxis('bottom')
        ### update
        #self.timer = QTimer()
        #self.timer.setInterval(500)
        #self.timer.timeout.connect(self.update_plot_data)
        #self.timer.start()
        #pen = pg.mkPen(color=(20,255,0))
        #p1.setRange(yRange=[0,100])
        #p1.setLabel('left', 'Amplitude (16bit Signed)')
        p2= self.OV
        p2.setYRange(21000,28000)
        p2.addLegend()
        p2.showGrid(x=False, y=True, alpha=0.8)
        penGy= pg.mkColor(240,240,240)
        p2.setBackground(penGy)
        ### data
        p2.x, p2.xc, p2.yc, p2.zc, p2.dSize= [], [], [], [], 0
        p2.xcLine= p2.plot(p2.x,p2.xc,pen='g')
        p2.ycLine= p2.plot(p2.x,p2.yc,pen='r')
        p2.zcLine= p2.plot(p2.x,p2.zc,pen='y')
        p2.getPlotItem().hideAxis('bottom')

    def updateP1(self):
        p1= self.OTH
        #global timelist
        #currentTime = datetime.now().strftime("%M.%S")
        if p1.dSize< 10:
            p1.x.append(p1.dSize)
            p1.t.append(dataTHList[0])#dataTHList[0])
            p1.h.append(dataTHList[1])#dataTHList[0])
            p1.dSize+= 1
            #timelist.append(currentTime)
        else:
            p1.x= [xc-1 for xc in p1.x[1:]]
            p1.x.append(p1.x[-1] + 1)
            p1.t= p1.t[1:]
            p1.t.append(dataTHList[0])
            p1.h= p1.h[1:]
            p1.h.append(dataTHList[1])
        p1.tLine.setData(p1.x, p1.t,clear=True)
        p1.hLine.setData(p1.x, p1.h,clear=True)
        self.OTemplcd.display(dataTHList[0])
        self.OHumilcd.display(dataTHList[1])
            #timelist= timelist[1:]
            #timelist.append(currentTime)
        #ax = p1.getAxis("bottom")
        #font= QtGui.QFont().setPixelSize(10)
        #ax.setStyle(tickFont= font)
        #ticks = list(enumerate(timelist))
        #ax.setTicks([ticks])

    def updateP2(self):
        p2= self.OV
        if p2.dSize< 10:
            p2.x.append(p2.dSize)
            p2.xc.append(dataVList[0])
            p2.yc.append(dataVList[1])
            p2.zc.append(dataVList[2])
            p2.dSize+= 1
        else:
            p2.x= [xc-1 for xc in p2.x[1:]]
            p2.x.append(p2.x[-1] + 1)
            p2.xc= p2.xc[1:]
            p2.xc.append(dataVList[0])
            p2.yc= p2.yc[1:]
            p2.yc.append(dataVList[1])
            p2.zc= p2.zc[1:]
            p2.zc.append(dataVList[2])
        p2.xcLine.setData(p2.x,p2.xc,clear=True)
        p2.ycLine.setData(p2.x,p2.yc,clear=True)
        p2.zcLine.setData(p2.x,p2.zc,clear=True)

    def runBox(self):
        self.initSerial(STR_COM)
        self.ser_data.write('/dcrun'.encode())

    def stopBox(self):
        try:
            self.ser_data.write('/dcstop'.encode())
        except:
            self.initSerial(STR_COM)
            self.ser_data.write('/dcstop'.encode())

    def powerBox(self):
        try:
            self.ser_data.write('/dcpower'.encode())
        except:
            self.initSerial(STR_COM)
            self.ser_data.write('/dcpower'.encode())

    def initSerial(self,STR_COM):
        self.ser_data= QSerialPort(
            STR_COM,
            baudRate= QSerialPort.Baud115200,
            readyRead= self.receive)
        self.ser_data.open(QIODevice.ReadWrite)
        if self.ser_data.isOpen():
            self.messageW('Zigbee-Client connected')
        else:
            self.messageW('Zigbee-Client disconnected')

    #@pyqtSlot()
    def receive(self):
        _data= self.ser_data.readLine().data().decode("utf-8") # read data
        #_data= b'/dt1522'.decode("utf-8")
        if _data != b'':
            global dataRxList, dataVList, dataTHList
            reV= 0
            reTH= 0
            dataRxList= list(filter(None,re.split('/d',_data)))
            #print(dataRxList)
            for i in range(len(dataRxList)):
                if dataRxList[i][0] in ['x','y','z'] and len(dataRxList[i])==6:
                    locV= ['x','y','z'].index(dataRxList[i][0])
                    dataVList[locV]= int(dataRxList[i][1:])*2
                    reV= 1
                    #print(dataVList)
                elif dataRxList[i][0] in ['t','h'] and len(dataRxList[i])==5:
                    locTH= ['t','h'].index(dataRxList[i][0])
                    dataTHList[locTH]= double(dataRxList[i][1:3]+'.'+dataRxList[i][3:])
                    reTH= 1
                elif dataRxList[i][0]== 'c':
                    self.messageW('databox'+ str(dataRxList[i][1:]))
                elif dataRxList[i][0]== 'b':
                    self.messageW('Zigbee-Server connected')
                else:
                    continue
        if reV== 1:
            self.updateP2()
        if reTH== 1:
            self.updateP1()

if __name__ == '__main__':
    app = QApplication([])
    window = sensorBoxUI()
    window.show()
    app.exec_()