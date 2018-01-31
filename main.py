import sys
import json
import time
import math
import dateutil
import requests
from PyQt4 import QtGui, QtCore
import matplotlib.pyplot as plt
from matplotlib import style
import matplotlib.animation as animation
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
style.use('ggplot')

class Window(QtGui.QWidget):

    def __init__(self):
        super(Window, self).__init__()
        self.time = []
        self.recorded_temp = []
        self.recorded_setpoint = []
        self.runtime = 0
        self.element_status = ""
        self.temp = 0
        self.setpoint = 0
        self.setWindowTitle("Distillation Control Panel")
        self.stacked_layout = QtGui.QStackedLayout()

        self.connect_page = QtGui.QWidget()
        self.home_page = QtGui.QWidget()
        self.home_UI()
        self.connect_UI()
        self.stacked_layout.addWidget(self.connect_page)
        self.stacked_layout.addWidget(self.home_page)
        self.setLayout(self.stacked_layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.show()

    def main(self):
        self.timer.start(1000)
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000)
        
    def home_UI(self):
        grid = QtGui.QGridLayout()
        runtime_indicator_label = QtGui.QLabel()
        self.runtime = QtGui.QLabel()
        runtime_indicator_label.setText("Runtime: ")
        element_status_indicator = QtGui.QLabel()
        self.element_status = QtGui.QLabel()
        element_status_indicator.setText("Element Status: ")
        temp_indicator_label = QtGui.QLabel()
        self.temp = QtGui.QLabel()
        temp_indicator_label.setText("Temperature: ")
        setpoint_label = QtGui.QLabel()
        self.setpoint = QtGui.QLabel()
        setpoint_label.setText("Setpoint: ")

        btn = QtGui.QPushButton("Adjust", self)
        btn.resize(btn.minimumSizeHint())
        self.setpoint_value = QtGui.QLineEdit()
        self.setpoint_value.setFixedWidth(btn.width())
        btn.clicked.connect(lambda: self.adjust_setpoint(self.setpoint_value.text()))

        self.fig = plt.figure(figsize=(15, 5))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        grid.addWidget(runtime_indicator_label, 0, 0, 2, 1)
        grid.addWidget(self.runtime, 0, 1, 2, 1)
        grid.addWidget(element_status_indicator, 0, 2, 2, 1)
        grid.addWidget(self.element_status, 0, 3, 2, 1)
        grid.addWidget(temp_indicator_label, 0, 4, 2, 1)
        grid.addWidget(self.temp, 0, 5, 2, 1)
        grid.addWidget(setpoint_label, 0, 6, 2, 1)
        grid.addWidget(self.setpoint, 0, 7, 2, 1)
        grid.addWidget(self.setpoint_value, 0, 8, 1, 1)
        grid.addWidget(btn, 1, 8, 1, 1)
        grid.addWidget(self.canvas, 3, 0, 1, 9)
        grid.addWidget(self.toolbar, 4, 0, 1, 9)
        self.home_page.setLayout(grid)
        self.setFocus()

    def connect_UI(self):
        '''
        User interface for connecting to distillation controller server. Enter local IP address for ESP8266 
        assigned by router
        '''
        grid = QtGui.QGridLayout()
        addr = QtGui.QLineEdit()
        addr.setPlaceholderText("Enter IP address for distiller server")
        grid.addWidget(addr, 1, 1)

        btn = QtGui.QPushButton("Connect!", self)
        btn.clicked.connect(lambda: self.connect(addr.text()))
        grid.addWidget(btn, 1, 2)
        self.connect_page.setLayout(grid)
        self.setFocus()

    def connect(self, addr):
        '''
        Check connection with controller server and verify address
        '''
        full_address = 'http://' + addr + "/connect"
        try:
            data = requests.get(str(full_address), timeout=1.0)
            if data.status_code == requests.codes.ok:
                QtGui.QMessageBox.information(self, 'test', "Connected!", QtGui.QMessageBox.Ok)
                self.address = addr
                self.stacked_layout.setCurrentIndex(1)
            else:
                # Add handling if non-200 http code returned
                pass
             
        except Exception:
            QtGui.QMessageBox.information(self, 'test', "Device not found at {}. Please enter a valid address".format(addr), QtGui.QMessageBox.Ok)
            self.connect_UI()
        
        self.main()

    def update_gui(self):
        full_address = 'http://' + self.address + "/request_data"
        data = json.loads(requests.get(full_address).text)
        runtime = convertMillis(data["Runtime"])
        temp = data['Temp']
        setpoint = data["Setpoint"]
        self.runtime.setText(runtime)
        self.element_status.setText(data["Element status"])
        self.temp.setText(str(temp))
        self.setpoint.setText(str(setpoint))

        self.time.append(dateutil.parser.parse(runtime))
        self.recorded_temp.append(temp)
        self.recorded_setpoint.append(setpoint)

    def adjust_setpoint(self, value):
        address = 'http://' + self.address + "/adjust_setpoint"
        if value != "":
            requests.post(address, json={'value': value})
            self.setpoint_value.setText("")

    def animate(self, i):
        plt.cla()
        self.ax.plot(self.time, self.recorded_temp, label="Outflow Temperature")
        self.ax.plot(self.time, self.recorded_setpoint, label="Controller Setpoint")
        self.ax.set_xlabel("Running Time", fontsize=8)
        self.ax.set_ylabel("Temperature (°C)", fontsize=8)
        plt.xticks(fontsize=8, rotation=45)
        plt.yticks(fontsize=8)
        plt.tight_layout()
        plt.legend(loc="upper left")
        self.canvas.draw()

def convertMillis(millis):
    seconds = math.floor((millis/1000)%60)
    minutes = math.floor((millis/(1000*60))%60)
    hours = math.floor((millis/(1000*60*60))%24)
    return "{:02}:{:02}:{:02}".format(hours, minutes, seconds)

def main():
    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()