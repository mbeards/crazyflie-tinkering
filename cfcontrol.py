import time
from threading import Thread
import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.utils import callbacks

logging.basicConfig(level=logging.DEBUG)

class Main:
  roll = 0.0
  pitch = 0.0
  yawrate = 0
  thrust = 10001

  def __init__(self):
    self.crazyflie = Crazyflie()
    cflib.crtp.init_drivers()

    available_radios = cflib.crtp.scan_interfaces()
    print available_radios
    #For now assume we want the 1st radio
    radio = available_radios[0][0]
    
    #Connect to the flie
    self.crazyflie.open_link(radio)

    self.crazyflie.connectSetupFinished.add_callback(self.connectSetupFinished)
    self.crazyflie.connectionFailed.add_callback(self.connectionLost)
    self.crazyflie.connectionLost.add_callback(self.connectionLost)

  def connectSetupFinished(self, linkURI):
    Thread(target=self.send_setpoint_loop).start()

    while 1:
      self.thrust = int(raw_input("Set thrust:"))

      if self.thrust==0:
        self.thrust = 10001
        self.send_setpoint()
        self.crazyflie.close_link()
      elif self.thrust<=10000:
        self.thrust = 10001
      elif self.thrust>=60000:
        self.thrust = 60000

  def send_setpoint_loop(self):
    while True:
      self.send_setpoint()
      time.sleep(0.1)

  def send_setpoint(self):
    self.crazyflie.commander.send_setpoint(self.roll, self.pitch, self.yawrate, self.thrust)

  def connectionLost(self, linkURI):
    print "CONNECTION LOST!"
    exit()

Main()
