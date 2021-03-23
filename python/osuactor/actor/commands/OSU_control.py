#!/usr/bin/env python
"""
  spectro_controller.py 
  Authors: Paul Martini, Richard Pogge, Klaus Honscheid (Ohio State) 
  Contact: martini.10@osu.edu 
  Documentation: See DESI-1133
  Last Major Update: 1 March 2016 (Winlight Lab Version) 
     Minor Update: 14 Dec 2016 (switch to E+E sensors, some code cleanup) 
     Minor Update: 25 Jan 2017 (switch Hartmann Doors to default off) 
     Minor Update: 21 Oct 2019 (added on and off actions to illuminator)
     Minor Update: 9 Jan 2020 (added option to flash illuminator with SSR)
"""

# Time until motor controller is ready to run commands after powered on
SclPowerSleep = 15.

# Device List used by motor controller communication code
devList = ["exp_shutter"]
shutterList = devList

# This list is used by the WAGO power control utilities
powList = ['exp_shutter_power']

# Device Addresses
devAddr = {"exp_shutter":("10.7.45.27",7776)}

devSock = {}
devConnected = {"exp_shutter":False}

#
# Commands for each device:
#

# Exposure Shutter Commands:
expCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4",
           "flash":"QX5","inflate":"QX6","deflate":"QX7", "on":"QX8",
           "off":"QX9","ssroff":"QX10","ssron":"QX11", "status":"IS"}

# Exposure Shutter Status: for inputs 1..8, index 0..7, [0status,1status]
expStat = [['sealDeflated','sealInflated'],
           ['ledDisabled','ledEnabled'],
           ['unused','unused'],
           ['unused','unused'],
           ['unused','unused'],
           ['unused','unused'],
           ['OPEN','CLOSED'],
           ['CLOSED','OPEN']]

import asyncio
import sys
import socket
import select
import errno
import os
import time
import datetime
import threading
from time import sleep 
from pymodbus3.client.sync import ModbusTcpClient as mbc

class Controller(): 
    software_version = "0.9" 	
    def __init__(self, unit = 0): 
        # Spectrograph Unit
        self.unit = unit
        # WAGO address -- 
        self.wagoHost = '10.7.45.27'
        # Controller Status dictionary 
        self.controller_status = {
            'status' : 'ERROR', 		# ERROR | READY | BUSY
            'exp_shutter' : 'ERROR',		# ERROR | OPEN | CLOSED
            'exp_shutter_power' : 'ON',	# ERROR | ON | OFF
            'updated' : datetime.datetime.utcnow().isoformat()
          } 
        self.sensors = {
            '40001' : -273., 
            '40002' : -1., 
            '40003' : -273., 
            '40004' : -1., 
            '40005' : -273., 		# IEB internal temp
            '40006' : -1.,
            '40009' : -273.,
            '40010' : -273.,
            '40011' : -273.,
            '40012' : -273.,
            'updated' : datetime.datetime.utcnow().isoformat()
          } 

    async def exp_shutter(self, position): 
        """  
        Operate the exposure shutter. Check the motor is on, and then move to the target position. 
        position = [open, close] 
        Note: this does not check the exposure status
        """  
  
        # Check for valid position
        if position == 'open': 
            command = 'open' 
        elif position == 'close': 
            command = 'close'
        else: 
            raise RuntimeError("ERROR in exp_shutter(): %s not one of [open, close]" % position) 
    
        # Check the EXP power status 
        if self.controller_status['exp_shutter_power'] == 'OFF' or self.controller_status['exp_shutter_power'] == 'ERROR': 
            raise RuntimeError("ERROR: exp_shutter power status %s" % self.controller_status['exp_shutter_power']) 
        # Operate the shutter
        status, sclReply = await SclCmd('exp_shutter', command) 
    
        if command == 'open':
            if sclReply == 'DONE': 
                self.controller_status['exp_shutter'] = 'OPEN' 
            else: 	# if fails, pause briefly and try one more time
                time.sleep(0.25) 
                await self.SclStatusUpdate('exp_shutter') 
                if self.controller_status['exp_shutter'] == 'ERROR':  
                  raise RuntimeError("ERROR in exp_shutter(): %s with command %s" % (sclReply, command) ) 
        elif command == 'close':
            if sclReply == 'DONE': 
                self.controller_status['exp_shutter'] = 'CLOSED' 
            else: 
                time.sleep(0.25) 
                await self.SclStatusUpdate('exp_shutter') 
                if self.controller_status['exp_shutter'] == 'ERROR':  
                  raise RuntimeError("ERROR in exp_shutter(): %s with command %s" % (sclReply, command) ) 
        else: 
            raise RuntimeError("ERROR in exp_shutter()") 

    async def SclStatusUpdate(self, device): 
        """
        Request a status update for device and update the 
        corresponding keywords in the controller_status data structure
        device = [exp_shutter, hartmann_left, hartmann_right] 
        """
      
        # Check that the device exists
        if device in devList == False:
            return False, "Error: %s is not a valid device" % device
    
        # Check that the device is powered on
        if self.controller_status[device+'_power'] != 'ON': 
            return False, "Error: %s power is not ON" % device
      
        # Request status from the device 
        status, sclReply = await SclCmd(device, 'status') 
    
        # Parse the reply, make sure it starts with 'IS' 
        (cmdStr,sepStr,argStr) = sclReply.partition("=")
        if cmdStr != 'IS':
            return False, "ERROR in SclStatusUpdate for %s" % device
    
        bitVal = []
        for i in range(8):
            bitVal.append(int(argStr[7-i]))
      
        # Exposure Shutter 
        if device == 'exp_shutter': 
            if bitVal[6]==bitVal[7]:	# Door is ajar
                self.controller_status['exp_shutter'] = 'ERROR'
            elif bitVal[6] == 1 and bitVal[7] == 0: 
                self.controller_status['exp_shutter'] = 'CLOSED' 
            elif bitVal[6] == 0 and bitVal[7] == 1: 
                self.controller_status['exp_shutter'] = 'OPEN' 
         
        self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
        return True, 'DONE' 

#################################################################
#
#  WAGO routines 
#
#################################################################

#---------------------------------------------------------------------------
#
# getWAGOEnv(): read all WAGO unit environmental sensors
#
# Read the environmental sensors (temperature and humidity) connected
# to the WAGO modbus controller and set the approriate values in the
# self.sensors data dictionary.
#
# Temperature is expressed in degrees Celsius
# Relative Humidity is expressed in Percent (%)
#
# Returns:
#   (status,msgStr)
# where:
#   status = True on success, with msgStr = DONE
#   status = False on errors, with msgStr containing a fault message
#
# This is normally invoked by the get() method with what='sensors'
#
# Updated to replace the Dwyer RH/T sensors with the E+E sensors that
# we'll use for the final controller system [rwp/osu]
#
#---------------------------------------------------------------------------
  
    async def getWAGOEnv(self):
  
        # WAGO register addresses and associated datum keywords in the
        # "sensors" dictionary
    
        # The E+E RH/Temp sensors are connected to an 8-port analog
        # input module on the WAGO modbus at address 40001 (logical
        # address 0).  Each sensor is connected to two adjacent ports:
        # RH then T.
  
        rhtAddr = 0
        rhtRHKeys = ['40002','40004','40006']
        rhtTKeys  = ['40001','40003','40005']
        numRHT  = len(rhtTKeys)

        # The RH and T measured is a linear function of the decimal
        # datum returned by the WAGO analog input module as follows:
        #      RH = RH0 + RHs*x  units: %RH
        #       T = T0 + Ts*x    units: degrees Celsius
        # Ranges:
        #   RH = 0-100%
        #    T = -30 to 70C
  
        RH0 = 0.0      # Humidity linear calibration
        RHs = 100.0/32767.0   # 100/(2^15-1)
        T0 = -30.0     # Temperature linear calibration
        Ts = RHs
    
        # The platinum RTDs are connected to a 4-port RTD module on
        # the WAGO modbus at address 40009 (logical address 8)
    
        rtdAddr = 8
        rtdKeys = ['40009','40010','40011','40012']
        numRTDs = len(rtdKeys)
    
        # Get a WAGO client handle and connect (port 502 is implicit
        # as per the modbus spec).
    
        wagoClient = mbc(self.wagoHost)
        if not wagoClient.connect():
            return False,"** ERROR: Cannot connect to WAGO at %s" % (self.wagoHost)
    
        # Read the Pt RTD Temperature Sensors
    
        rd = wagoClient.read_holding_registers(rtdAddr,numRTDs)
        for i in range(numRTDs):
            self.sensors[rtdKeys[i]] = round(await ptRTD2C(float(rd.registers[i])), 2) 

    
        # Read the E+E RH/T sensors and convert to physical units.
  
        rd = wagoClient.read_holding_registers(rhtAddr,2*numRHT)
        for i in range(numRHT):
            self.sensors[rhtRHKeys[i]] = round(RH0 + RHs*float(rd.registers[2*i]), 2) 
            self.sensors[rhtTKeys[i]] = round(T0 + Ts*float(rd.registers[2*i+1]), 2) 
    
        # All done, clean up and return success
        self.sensors['updated'] = datetime.datetime.utcnow().isoformat()
    
        wagoClient.close()
        return True, 'DONE' 
  
 #---------------------------------------------------------------------------
 #
 # getWAGOPower(self)
 #
 # Returns the power state of all DESI devices controlled by the
 # WAGO modbus unit.
 #
 # Sets the appropriate entry in the self.controller_status
 # dictionary with the current state, "on" or "off"
 #
 # Returns:
 #   (status,msgStr)
 # where:
 #   status = True on success, with msgStr = DONE
 #   status = False on errors, with msgStr containing a fault message
 #
 # See also: setWAGOPower()
 #
 #---------------------------------------------------------------------------
  
    async def getWAGOPower(self):
  
        # 8-port digital output register address
    
        do8Addr = 512
        maxPorts = 8
    
        # Mapping between 8DO ports and Desi devices
    
    
        numDevs = len(powList)
    
        # Get a WAGO client handle and connect (port 502 is implicit as
        # per modbus spec).
    
        wagoClient = mbc(self.wagoHost)
        if not wagoClient.connect():
            return False,"** ERROR: Cannot connect to WAGO at %s" % (self.wagoHost)
        # Read the output data, and translate into "on" and "off"
        # states. The outputs are different for the shutters and doors. 
        # For the shutters: 
        #   Relay is closed means shutter motor controller powered on. 
        #   To turn off, open the relay         
        #     datum = True, power = OFF
        #     datum = False, power = ON
        # For the doors: 
        #   Relay is closed means shutter motor controller powered off. 
        #   To turn on, open the relay         
        #     datum = False, power = OFF
        #     datum = True, power = ON
        # Note: this is a change from pre-Jan2018 versions [PM] 
    
        rd = wagoClient.read_holding_registers(do8Addr,maxPorts)
        outState = await wagoDOReg(rd.registers[0],numOut=maxPorts)

        for i in range(numDevs):
            if i == 0 or i == 1: # shutters 
              if outState[i]:
                  self.controller_status[powList[i]] = "OFF"
              else:
                  self.controller_status[powList[i]] = "ON"
            if i == 2 or i == 3: # shutters 
              if outState[i]:
                  self.controller_status[powList[i]] = "ON"
              else:
                  self.controller_status[powList[i]] = "OFF"
        
        # All done, clean up and return success
        self.sensors['updated'] = datetime.datetime.utcnow().isoformat()
 
        wagoClient.close()
        return True,'DONE'

##################################################################
# Low-level routines 
##################################################################


async def SclCmd(dev, command, SelectTimeout=0.5):
    # This function checks that the device exists, that the command is
    # valid for the device, opens a socket to the device, sends the command,
    # and queries the socket with a select loop until complete or timeout
    # Returns:
    #   state: True = success, False=fault
    #   resultStr: string with command result or error if state=False
         
    # Check that the device exists
    if dev in devList == False:
        return False, "Error: %s is not a valid device" % dev
  
    # Check that the command sclCmd is legal for the device
    # Note: The status command is distinct, as it is valid for any device, 
    # and it runs a low-level command, not an entire segment 
    if command == 'status':
        sclCmd = "IS"
    elif dev == 'exp_shutter': 
      if command in expCmds == False: 
        return False, "Error: %s is not a valid %s command" % (command, dev) 
      else:
        sclCmd = expCmds[command]
    else: 
      return False, "Error: %s and %s combination not found" % (command, dev)
  
    if command == 'status':
      SelectTimeout = 1.
    if dev == 'exp_shutter': 
      if command == 'home': 
        SelectTimeout = 4.
  
    # Connect to the mechanism 
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.setblocking(True)
    devSock[dev] = sock
    reqDev = dev
  
    try:
      devSock[dev].connect(devAddr[dev])
      devConnected[dev] = True
    except:
      devConnected[dev] = False
      return False, "Error: Could not connect the %s" % (dev)
  
    status, reply = await sendSclCmd(reqDev, sclCmd)
  
    # Start the select loop to read the socket
  
    keepGoing = True
    while keepGoing:
      inFDList = [devSock[dev]]
      outFDList = []
      if SelectTimeout > 0.0:
        readable,writeable,exceptional=select.select(inFDList,outFDList,inFDList,SelectTimeout)
      else:
        readable,writeable,exceptional=select.select(inFDList,outFDList,inFDList)
  
      if not (readable or writeable or exceptional):
        devSock[dev].close()
        return False, 'ERROR: %s timed out' % (command) 
      for s in readable:
        if s is devSock[dev]:
          fromSock = True
          sclReply = ""
          replyDev = dev
          try:
            #recStr = devSock[dev].recv(4096) # this blocks... beware!
            recStr = devSock[dev].recv(4096).decode() # this blocks... beware!
            sclReply = recStr[2:-1]  # strip opcode header and terminator
          #except socket.error, err:
          except socket.error as err:
            if err.errno == errno.ECONNRESET:
              devSock[dev].close()
              sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
              sock.setblocking(True)
              sock.connect(devAddr[dev])
              devSock[dev] = sock
            else:
              devSock[dev].close() 
              return False, "ERROR: Caught recv() exception: %s" % (os.strerror(err.errno))
  
          # Return if sclReply is done 
          if len(sclReply) > 0:
            if sclReply[:4] == 'DONE':
              devSock[dev].close()
              return True, sclReply
            if sclReply[:3] == 'ERR':
              devSock[dev].close()
              return True, sclReply
            if sclReply[:2] == 'IS':
              devSock[dev].close()
              return True, sclReply
  
      # handle exceptions on the select() call
      for s in exceptional:
          return False, 'Handling exception condition for',s.getpeername()


#---------------------------------------------------------------------------
#
# Send a command to an SCL controller socket
#
# Returns:
#    state: True = success, False=fault
#    resultStr: string with command result or error if state=False
#
#---------------------------------------------------------------------------

async def sendSclCmd(dev,cmdStr):

    if dev not in devList:
        return False,"ERROR: Invalid device %s requested" % (dev)

    if not devConnected[dev]:
        return False,"ERROR: %s is not connected" % (dev)

    # Header and tail for the eSCL command packet

    sclHead = chr(0)+chr(7)
    sclTail = chr(13)

    # build the command packet

    sclStr = await str2scl(cmdStr)

    # Send it

    #devSock[dev].sendall(sclStr)
    devSock[dev].sendall(sclStr.encode())
    return True,'STATUS: %s command sent to %s' % (cmdStr,dev)

#----------------------------------------------------------------
#
# str2scl() - return a string wrapped in an SCL command packet
#
# Return an SCL command packet for a string.  Also forces the
# string to uppercase as required by SCL.
#
#----------------------------------------------------------------

async def str2scl(cmdStr):
    sclHead = chr(0)+chr(7)
    sclTail = chr(13)
    sclStr = sclHead + cmdStr.upper() + sclTail  # build the packet
    return sclStr



#---------------------------------------------------------------------------
#
# WAGO I/O convenience functions
#
#---------------------------------------------------------------------------

#----------------------------------------------------------------
#
# ptRTD2C - convert RTD ADU to degrees C
#
# inputs:
#    rawRTD = raw RTD ADU readout from the WAGO unit
# returns:
#    temperature in degrees C
#
# This function converts RTD output to degrees C for 
# a WAGO 750-461/753-461 2-Channel Analog RTD module
#

async def ptRTD2C(rawRTD):
    tempRes = 0.1   # module resolution is 0.1C per ADU
    tempMax = 850.0 # maximum temperature for a Pt RTD in deg C
    wrapT = tempRes*((2.0**16)-1) # ADU wrap at <0C to 2^16-1

    temp = tempRes*rawRTD
    if temp > tempMax:
        temp -= wrapT

    return temp

#----------------------------------------------------------------
#
# wagoDOReg - WAGO Digital Output register datum converter
#
# input: 
#   rd = register datum (integer 0..255)
#   numOut = number of outputs (default: 8)
# output:
#   numOut-element list of booleans, True=On, False=Off
#
# Translates an 8-bit unsigned integer register datum returned by a
# WAGO digital output unit into True/False state flags
#
#----------------------------------------------------------------

async def wagoDOReg(rd,numOut=8):
    testOut = []
    for i in range(numOut):
        testOut.append((rd & 2**i) == 2**i)
    return testOut


