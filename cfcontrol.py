import time
from threading import Thread
import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.utils import callbacks
from cfclient.utils.logconfigreader import LogConfig
from cfclient.utils.logconfigreader import LogVariable

from OSC import OSCServer, OSCMessage

logging.basicConfig(level=logging.DEBUG)

class Main:
  roll = 0.0
  pitch = 0.0
  yawrate = 0
  thrust = 10001

  def __init__(self):

    self.server = OSCServer (("0.0.0.0", 8000))
    self.server.addMsgHandler("/1/rollpitch", self.roll_pitch_callback)
    self.server.addMsgHandler("/1/yawthrust", self.yaw_thrust_callback)
    self.server.addMsgHandler("/1/stop", self.stop_callback)
    self.server.addMsgHandler("/1/hovermode", self.hovermode_callback)
  

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
    Thread(target=self.osc_loop).start()
    self.crazyflie.param.set_value("stabilizer.debug", "0")
    self.crazyflie.param.add_update_callback("stabilizer.debug", self.paramUpdateCallback)
    self.crazyflie.param.add_update_allback("stabilizer.mode", self.paramUpdateCallback)


  def paramUpdateCallback(self, name, value):
    print "%s has value %d" % (name, value)

  def accel_log_callback(self, data):
    logging.info("Accelerometer: x+%.2f, y=%.2f, z=%.2f" % (data["acc.x"], data["acc.y"], data["acc.z"]))

  def osc_loop(self):
    while True:
      self.server.handle_request()

  def roll_pitch_callback(self, path, tags, args, source):
    #print ("path", path)
    #print ("args", args)
    #print ("source", source)
    print "ROLL", args[0]
    #self.roll=(args[0]*180)-90
    self.roll=(args[0]*90)-45
    print "PITCH", args[1]
    #self.pitch=(180*args[1])-90
    self.pitch=(args[1]*90)-45
  def yaw_thrust_callback(self, path, tags, args, source):
    #print ("path", path)
    #print ("args", args)
    #print ("source", source)
    print "YAW", (180*args[1])-90
    print "THRUST", (49999*args[0])+10001
    self.thrust = (49999*args[0]) + 10001
    self.yawrate = (args[1]*90)-45
  def stop_callback(self, path, tags, args, source):
    self.crazyflie.param.set_value("stabilizer.debug", "1")
    self.thrust = 0
    self.send_setpoint()
    self.crazyflie.close_link()
    exit()
  def hovermode_callback(self, path, tags, args, source):
    if args[0]:
      logging.info("Entering hover mode.")
      self.crazyflie.param.set_value("stabilizer.mode", "1")
    else:
      logging.info("Exiting hover mode.")
      self.crazyflie.param.set_value("stabilizer.mode", "0")


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
