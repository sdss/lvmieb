#added by CK 2021/03/30

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

from __future__ import annotations, print_function, division, absolute_import

import asyncio
import configparser
import os
import re
import warnings
import datetime

from lvmieb.exceptions import LvmIebError, LvmIebWarning
from typing import Any, Callable, Iterable, Optional

import numpy
from clu.device import Device

from pymodbus.client.asynchronous.async_io import AsyncioModbusTcpClient as ModbusClient


__all__ = ["IebController"]

# Device list

devList = ["shutter","hartmann_left","hartmann_right"]


#Exposure shutter commands
expCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4",

           "flash":"QX5","inflate":"QX6","deflate":"QX7", "on":"QX8",

           "off":"QX9","ssroff":"QX10","ssron":"QX11", "status":"IS"}

# Hartmann Door commands
hdCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4","status":"IS"}

# This list is used by the WAGO power control utilities
powList = ['exp_shutter_power', 
            'hartmann_left_power', 
            'hartmann_right_power']

class IebController:
    """
            Talks to an Ieb controller over TCP/IP
    """
    count = 0
    
    def __init__(self, host: str, port: int, name: str = ""):
        #Device.__init__(self, host, port)
        self.name = name #must use it!!_C

        self.sensors = {
            'rhtT1(40001)' : -273., 		# Temperatures in C
            'rhtRH1(40002)' : -1., 	# Humidity in percent
            'rhtT2(40003)' : -273.,
            'rhtRH2(40004)' : -1.,
            'rtd1(40009)' : -273., 		# IEB internal temp
            'rtd2(40010)' : -273.,		# Bench temp near NIR camera
            'rtd3(40011)' : -273., 		# Bench temp near collimator
            'rtd4(40012)' : -273. 		# Bench temp near cryostats
          }
          
        self.__status_event = asyncio.Event()
        self.reader = None
        self.writer = None
        self.hartmann_right_status = None
        self.hartmann_left_status = None
        self.shutter_status = None
        self.lock = asyncio.Lock()
        self.host = host
        self.port = port

    async def send_command(self, command, SelectTimeout= 1):
        """
        Parses the high level command (open, close, status) to low level commands and send 
        to the motor controller controlling the exposure shutter, hartmann door. reads the reply from the motor
        """
        """
        print(f"initial count : {self.count}")
        if self.count > 0:
            await self.lock.acquire()
            print(f"after acquire count : {self.count}")
        
        self.count +=1
        """
        
        current_time = datetime.datetime.now()
        print('when send command              : %s', current_time)     
        
        #check that the device exists
        if self.name in devList == False:
            raise LvmIebError(f"%s is not a valid device" %self.name)
        
        #check that the command is legal for the device
        if self.name == "shutter":
            if command in expCmds == False:
                raise LvmIebError(f"%s is not a valid %s command" % (command, self.name))
            else:
                c_message = expCmds[command]
        elif self.name == "hartmann_left" or self.name == "hartmann_right":
            if command in hdCmds == False:
                raise LvmIebError(f"%s is not a valid %s command" % (command, self.name))
            else:
                c_message = hdCmds[command]
        else:
            raise LvmIebError(f"%s and %s combination not found" % (command, self.name))
        
        #get the status from the hardware 
        if command != 'status':
            try:
                if self.name == 'shutter':
                    self.shutter_status = await self.get_status()
                elif self.name == 'hartmann_right':
                    self.hartmann_right_status = await self.get_status()
                elif self.name == 'hartmann_left':
                    self.hartmann_left_status = await self.get_status()
            except:
                raise LvmIebError(f"Could not connect the %s" %self.name)
            
        #check the shutter& harmann door status before open and close
        if self.name == "shutter":
            if command == "open":
                if self.shutter_status == "opened":
                    raise LvmIebError(f"The shutter is already {self.shutter_status}!")
            elif command == "close":
                if self.shutter_status == "closed":
                    raise LvmIebError(f"The shutter is already {self.shutter_status}!")
        elif self.name == "hartmann_right":
            if command == "open":
                if self.hartmann_right_status == "opened":
                    raise LvmIebError(f"The hartmann right door is already {self.hartmann_right_status}!")
            elif command == 'close':
                if self.hartmann_right_status == "closed":
                    raise LvmIebError(f"The hartmann right door is already {self.hartmann_right_status}!")
        elif self.name == "hartmann_left":
            if command == "open":
                if self.hartmann_left_status == "opened":
                    raise LvmIebError(f"The hartmann left door is already {self.hartmann_left_status}!")
            elif command == "close":
                if self.hartmann_left_status == "closed":
                    raise LvmIebError(f"The hartmann right door is already {self.hartmann_left_status}!")

        #Tweak timeouts
        if self.name == "hartmann_left" or self.name == "hartmann_right":
            if command == "open" or command == "close" or command == "home":
                SelectTimeout = 4.0
        if self.name == "shutter":
            if command == "home":
                SelectTimeout = 4.0

        if command != "status":
                        
            #connection
            current_time = datetime.datetime.now()
            print('before connection              : %s', current_time)
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            current_time = datetime.datetime.now()
            print('after connection               : %s', current_time)     
        else:
            #connection
            current_time = datetime.datetime.now()
            print('before connection              : %s', current_time)
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            current_time = datetime.datetime.now()
            print('after connection               : %s', current_time)

        # parse the low-level command to the hardware
        sclHead = chr(0)+chr(7)
        sclTail = chr(13)
        sclStr = sclHead + c_message.upper() + sclTail

        try:
            current_time = datetime.datetime.now()
            print('before write command           : %s', current_time)     
            self.writer.write(sclStr.encode())        
            current_time = datetime.datetime.now()
            print('after write command            : %s', current_time)     
            await self.writer.drain()        
            current_time = datetime.datetime.now()
            print('after write drain              : %s', current_time)     
        except:
            self.writer.close()
            await self.writer.wait_close()                
            raise LvmIebError(f"Failed to write the data")
        
        #read byte stream from the motor controller
        try:            
            current_time = datetime.datetime.now()
            print('before readuntil               : %s', current_time)     
            reply = await asyncio.wait_for(self.reader.readuntil(b"\r"), SelectTimeout)
            current_time = datetime.datetime.now()
            print('after readuntil                : %s', current_time)     
        except:
            self.writer.close()
            await self.writer.wait_closed()
            raise LvmIebError(f"failed to read the data")

        #disconnect device 
        try:
            current_time = datetime.datetime.now()
            print('before close writer            : %s', current_time)     
            self.writer.close()
            await self.writer.wait_closed()
            current_time = datetime.datetime.now()
            print('after close writer             : %s', current_time)     
        except:
            raise LvmIebError(f"Could not disconnect the %s" %self.name)

        if command == "status" and reply:
            if self.name == "shutter":
                assert isinstance(reply, bytes)
                shutter_stat = parse_IS(reply)
                self.shutter_status = shutter_stat
                return shutter_stat
            elif self.name == "hartmann_left":
                assert isinstance(reply, bytes)
                hartmann_stat = parse_IS(reply)
                self.hartmann_left_status = hartmann_stat
                return hartmann_stat
            elif self.name == "hartmann_right":
                assert isinstance(reply, bytes)
                hartmann_stat = parse_IS(reply)
                self.hartmann_right_status = hartmann_stat
                return hartmann_stat        
        elif b"DONE" in reply:
            #updating the status of each hardware
            if self.name == "shutter":
                self.shutter_status = await self.get_status()
                return self.shutter_status
            elif self.name == "hartmann_right":
                self.hartmann_right_status = await self.get_status()
                return self.hartmann_right_status
            elif self.name == "hartmann_left":
                self.hartmann_left_status = await self.get_status()
                return self.hartmann_left_status
        elif b"ERR" in reply:
            raise LvmIebError(f"Error in the controller, please check the hardware")


    async def get_status(self):
        
        r, w = await asyncio.open_connection(self.host, self.port)
        
        # parse the low-level command to the hardware
        message = 'IS'
        SelectTimeout = 1
        
        sclHead = chr(0)+chr(7)
        sclTail = chr(13)
        sclStr = sclHead + message.upper() + sclTail
        
        try:
            w.write(sclStr.encode())
            await w.drain()
        except:
            w.close()
            await w.wait_close()                
            raise LvmIebError(f"Failed to write the data")
        
        #read byte stream from the motor controller
        try:
            reply = await asyncio.wait_for(r.readuntil(b"\r"), SelectTimeout)
        except:
            w.close()
            await w.wait_closed()
            raise LvmIebError(f"failed to read the data")
        
        try:
            w.close()
            await w.wait_closed()
        except:
            raise LvmIebError(f"Could not disconnect the %s" %self.name)
        
        if message == "IS" and reply:
            assert isinstance(reply, bytes)
            stat = parse_IS(reply)
            return stat
        
    # courutine for receiving data from the WAGO module

    async def getWAGOEnv(self):

        rtdAddr = 8

        rtdKeys = ['rtd1(40009)',
                   'rtd2(40010)',
                   'rtd3(40011)',
                   'rtd4(40012)']
        numRTDs = len(rtdKeys)

        rhtRHKeys = ['rhtRH1(40002)',
                     'rhtRH2(40004)']
        rhtTKeys = ['rhtT1(40001)',
                    'rhtT2(40003)']
        numRHT = len(rhtTKeys)
        rhtAddr = 8

        RH0 = 0.0
        RHs = 100.0/32767.0
        T0 = -30.0
        Ts = RHs

        wagoClient = ModbusClient(self.host, self.port)
        
        await wagoClient.connect()
        
        rd = await wagoClient.protocol.read_holding_registers(rtdAddr, numRTDs)
        for i in range(4):
            self.sensors[rtdKeys[i]] = round(ptRTD2C(float(rd.registers[i])), 2)

        rd = await wagoClient.protocol.read_holding_registers(rhtAddr,2*numRHT)

        for i in range(2):
            self.sensors[rhtRHKeys[i]] = round(RH0 + RHs*float(rd.registers[2*i]), 2)
            self.sensors[rhtTKeys[i]] = round(T0 + Ts*float(rd.registers[2*i+1]), 2)

        wagoClient.protocol.close()
        return True
    
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
        outState = wagoDOReg(rd.registers[0],numOut=maxPorts)

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

def ptRTD2C(rawRTD):
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

def wagoDOReg(rd,numOut=8):
    testOut = []
    for i in range(numOut):
        testOut.append((rd & 2**i) == 2**i)
    return testOut

# low level command to parse the byte stream from the motor controller

def parse_IS(reply: bytes):

    match = re.search(b"\x00\x07IS=([0-1])([0-1])[0-1]{6}\r$", reply)
    if match is None:
        return False

    if match.groups() == (b"1", b"0"):
        return "opened"
    elif match.groups() == (b"0", b"1"):
        return "closed"
    else:
        return False