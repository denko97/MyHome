import os
import sys
import random
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
from mqtt_init import *

# Creating Client name - should be unique 
global clientname
r = random.randrange(1, 10000000)
clientname = "IOT_client-Id-" + str(r)


class Mqtt_client():
    
    def __init__(self):
        # broker IP address:
        self.broker = ''
        self.port = 0
        self.clientname = ''
        self.username = ''
        self.password = ''
        self.on_connected_to_form = ''
        self.temp_threshold = 27
        self.dust_threshold = 40
        self.lock_status = ''

       
       
        
    # Setters and getters
    def set_on_connected_to_form(self, on_connected_to_form):
        self.on_connected_to_form = on_connected_to_form
    def get_broker(self):
        return self.broker
    def set_broker(self, value):
        self.broker = value
    def get_port(self):
        return self.port
    def set_port(self, value):
        self.port = value
    def get_clientName(self):
        return self.clientname
    def set_clientName(self, value):
        self.clientname = value
    def get_username(self):
        return self.username
    def set_username(self, value):
        self.username = value
    def get_password(self):
        return self.password
    def set_password(self, value):
        self.password = value
        
    def on_log(self, client, userdata, level, buf):
        print("log: " + buf)
            
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("connected OK")
            self.on_connected_to_form()
        else:
            print("Bad connection Returned code=", rc)
            
    def on_disconnect(self, client, userdata, flags, rc=0):
        print("Disconnected result code " + str(rc))
            
    def on_message(self, client, userdata, msg):
        topic = msg.topic
        m_decode = str(msg.payload.decode("utf-8", "ignore"))
        if topic == temp_topic:
             temp = float(m_decode.split('Temperature: ')[1])
             print(f"Message received from: {topic}, Temperature: {temp}°C")
             mainwin.connectionDock.update_data('Temperature',temp)
             self.check_temp(temp)
            
        elif topic == dust_topic:
            dust = float(m_decode.split('Dust: ')[1])
            print(f"Message received from {topic}, Dust Level: {dust}")
            mainwin.connectionDock.update_data('Dust',dust)
            self.check_dust(dust)
            
        elif topic == lock_topic[0]:
            print(f"Message received from:{lock_topic[0]}, Lock is: {m_decode}")
            self.check_lock(m_decode)
        

        
    def check_temp(self, temp):
        if temp > self.temp_threshold:
            print(f"Temperature exceeds {self.temp_threshold}°C")
            self.publish_to(app_topic, "It's time to turn on the Air Conditioner!", retain = False)

    def check_dust(self, dust):
        if dust > self.dust_threshold:
            print(f"Dust level exceeds {self.dust_threshold} ")
            self.publish_to(app_topic, "It's getting dusty here! Robot start to cleaning.", retain = False)

    def check_lock(self, status):
        if status == 'Locked':
                self.lock_status = True
                mainwin.connectionDock.update_data('Lock',status)
                self.publish_to(app_topic, "The door is secure.", retain = True)
        elif status == 'Unlocked':
                self.lock_status = False
                mainwin.connectionDock.update_data('Lock',status)
                self.publish_to(app_topic, "The door is unlocked! If this wasn't you, please check it immediately.", retain = True)

           

    def connect_to(self):
        # Init paho mqtt client class
        self.client = mqtt.Client(self.clientname, clean_session=True) # create new client instance
        self.client.on_connect = self.on_connect  # bind call back function
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        print("Connecting to broker ", self.broker)
        self.client.connect(self.broker, self.port)  # connect to broker
    
    def disconnect_from(self):
        self.client.disconnect()
    
    def start_listening(self):
        self.client.loop_start()
    
    def stop_listening(self):
        self.client.loop_stop()
    
    def subscribe_to(self, topic):
        self.client.subscribe(topic)
              
    def publish_to(self, topic, message, retain=False):
        self.client.publish(topic, message, retain = retain)
        
class ConnectionDock(QDockWidget):
    """Main """
    def __init__(self, mc):
        QDockWidget.__init__(self)
        
        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)
        self.eHostInput = QLineEdit()
        self.eHostInput.setInputMask('999.999.999.999')
        self.eHostInput.setText(broker_ip)
        
        self.ePort = QLineEdit()
        self.ePort.setValidator(QIntValidator())
        self.ePort.setMaxLength(4)
        self.ePort.setText(broker_port)
        
        self.eClientID = QLineEdit()
        global clientname
        self.eClientID.setText(clientname)
        
        self.eUserName = QLineEdit()
        self.eUserName.setText(username)
        
        self.ePassword = QLineEdit()
        self.ePassword.setEchoMode(QLineEdit.Password)
        self.ePassword.setText(password)
        
        self.eKeepAlive = QLineEdit()
        self.eKeepAlive.setValidator(QIntValidator())
        self.eKeepAlive.setText("60")
        
        self.eSSL = QCheckBox()
        
        self.eCleanSession = QCheckBox()
        self.eCleanSession.setChecked(True)
        
        self.eConnectbtn = QPushButton("Enable/Connect", self)
        self.eConnectbtn.setToolTip("click me to connect")
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet("background-color: gray")

        self.Temperature=QLineEdit()
        self.Temperature.setText('')

        self.Dust=QLineEdit()
        self.Dust.setText('')

        self.Lock=QLineEdit()
        self.Lock.setText('')

        self.eLockBtn = QPushButton("Lock", self)
        self.eLockBtn.setToolTip("Click to Lock/Unlock")
        self.eLockBtn.setStyleSheet("background-color: darkgrey")
        self.eLockBtn.clicked.connect(self.toggle_lock)

        formLayout = QFormLayout()
        formLayout.addRow("Turn On/Off", self.eConnectbtn)
        formLayout.addRow("Temperature:", self.Temperature)
        formLayout.addRow("Dust Level:", self.Dust)
        formLayout.addRow("Lock Status:", self.Lock)
        formLayout.addRow("Lock/Unlock", self.eLockBtn)
        

        widget = QWidget(self)
        widget.setLayout(formLayout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)     
        self.setWindowTitle("Connect")
        
    def on_connected(self):
        self.eConnectbtn.setStyleSheet("background-color: green")

                    
    def on_button_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.set_username(self.eUserName.text())
        self.mc.set_password(self.ePassword.text())        
        self.mc.connect_to()        
        self.mc.start_listening()
        topics = [temp_topic, lock_topic[0], dust_topic]
        for topic in topics:
            self.mc.subscribe_to(topic)
        

    

    def toggle_lock(self):
        if self.mc.lock_status:
            self.mc.publish_to(lock_topic[1], "Unlock")

        else:
            self.mc.publish_to(lock_topic[1], "Lock")
            
       
        
    def update_data(self, sensor, data):
        if sensor == 'Temperature':
            self.Temperature.setText(str(data))
        elif sensor == 'Dust':
            self.Dust.setText(str(data))
        elif sensor == 'Lock':
            if data == "Locked":
                self.Lock.setText("Locked")
                self.eLockBtn.setText("Unlock")
                self.eLockBtn.setStyleSheet("background-color: darkgrey")
            elif data == 'Unlocked':
                self.Lock.setText("Unlocked")
                self.eLockBtn.setText("Lock")
                self.eLockBtn.setStyleSheet("background-color: red")

    

        
class MainWindow(QMainWindow):
    
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
                
        # Init of Mqtt_client class
        self.mc = Mqtt_client()
        
        # general GUI settings
        self.setUnifiedTitleAndToolBarOnMac(True)

        # set up main window
        self.setGeometry(30, 300, 500, 250)
        self.setWindowTitle('MyHome')  

        # Init QDockWidget objects        
        self.connectionDock = ConnectionDock(self.mc)        
        
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
