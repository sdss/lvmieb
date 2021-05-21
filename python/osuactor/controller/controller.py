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

from osuactor.exceptions import OsuActorError, OsuActorWarning
from typing import Any, Callable, Iterable, Optional

import numpy
from clu.device import Device

from pymodbus.client.sync import ModbusTcpClient as ModbusClient
#from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
#from pymodbus.client.asynchronous import schedulers

__all__ = ["OsuController"]


# Device list

devList = ["shutter","hartmann_left","hartmann_right"]


#Exposure shutter commands

expCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4",

           "flash":"QX5","inflate":"QX6","deflate":"QX7", "on":"QX8",

           "off":"QX9","ssroff":"QX10","ssron":"QX11", "status":"IS"}

# Hartmann Door commands

hdCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4","status":"IS"}

class OsuController(Device):
    """
            Talks to an OSU controller over TCP/IP
    """
    def __init__(self, host: str, port: int, name: str = ""):
        Device.__init__(self, host, port)
        self.name = name #must use it!!_C

        self.shutter_status = self.send_command("status")
        self.sensors = {
            'rhtT1(40001)' : -273., 		# Temperatures in C
            'rhtRH1(40002)' : -1., 	# Humidity in percent
            'rhtT2(40003)' : -273.,
            'rhtRH2(40004)' : -1.,
            'rhtT3(40005)' : -273.,
            'rhtRH3(40006)' : -1.,
            'rtd1(40009)' : -273., 		# IEB internal temp
            'rtd2(40010)' : -273.,		# Bench temp near NIR camera
            'rtd3(40011)' : -273., 		# Bench temp near collimator
            'rtd4(40012)' : -273. 		# Bench temp near cryostats
        #    'updated' : datetime.datetime.utcnow().isoformat()
          }
          

        self.__status_event = asyncio.Event()
        self.connected = False


    async def connect(self):
        """connect with devices"""

        if self.connected == False:
            try:
                self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
                self.connected = True
            except:
                self.connected = False
                raise OsuActorError(f"Could not connect the %s" %self.name)
            return False
        else:
            raise OsuActorError(f"The %s is already connected!" %self.name)

        return True

    async def disconnect(self):
        """close the connect"""

        if self.connected == True:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except:
                raise OsuActorError(f"Could not connect the %s" %self.name)
            return False
        else:
            raise OsuActorError(f"The %s is dicennected!" %self.name)

        return True
        

    async def send_command(self, command, SelectTimeout= 1):

        #check that the device exists
        if self.name in devList == False:
            raise OsuActorError(f"%s is not a valid device" %self.name)
            return False
        
        #check that the command is legal for the device
        if self.name == "shutter":
            if command in expCmds == False:
                raise OsuActorError(f"%s is not a valid %s command" % (command, self.name))
                return False
            else:
                c_message = expCmds[command]
        elif self.name == "hartmann_left" or self.name == "hartmann_right":
            if command in hdCmds == False:
                raise OsuActorError(f"%s is not a valid %s command" % (command, self.name))
                return False
            else:
                c_message = hdCmds[command]
        else:
            raise OsuActorError(f"%s and %s combination not found" % (command, self.name))
            return False

        #check the shutter status before open and close
        if self.connected == True:
            if self.name == "shutter":
                if command == "open":
                    if self.shutter_status == "open":
                        raise OsuActorError(f"The shutter is already {self.shutter_status}!")
                        return False
                elif command == "close":
                    if self.shutter_status == "close":
                        raise OsuActorError(f"The shutter is already {self.shutter_status}!")
                        return False

        #Tweak timeouts
        if self.name == "hartmann_left" or self.name == "hartmann_right":
            if command == "open" or command == "close" or command == "home":
                SelectTimeout = 4.0
        if self.name == "shutter":
            if command == "home":
                SelectTimeout = 4.0

        # parse the low-level command to the hardware
        sclHead = chr(0)+chr(7)
        sclTail = chr(13)
        sclStr = sclHead + c_message.upper() + sclTail
        if self.connected == True:
            try:
                self.writer.write(sclStr.encode())
                await self.writer.drain()
            except:
                raise OsuActorError(f"Failed to write the data")
                self.writer.close()
                await self.writer.wait_close()
                return False
        else:
            raise OsuActorError(f"Could not connect the %s" %self.name)
            return False

        try:
            reply = await asyncio.wait_for(self.reader.readuntil(b"\r"), SelectTimeout)
        except:
            self.writer.close()
            await self.writer.wait_closed()
            raise OsuActorError(f"failed to read the data")
            return False

        if command == "status" and reply:
            assert isinstance(reply, bytes)
            shutter_stat = parse_IS(reply)
            self.shutter_status = shutter_stat
            return shutter_stat
        else:
            if command == "open":
                self.shutter_status = "open"
            elif command == "close":
                self.shutter_status = "close"

            if reply != b"\x00\x07%\r":
                return False
            else:
                await asyncio.sleep(0.61)
                reply = await self.reader.readuntil(b"\r")
                if b"DONE" in reply:
                    return True
                else:
                    return False

        

    async def receive_status(self, areader, timeout, cmd):
        
        KeepGoing = True

        while KeepGoing:

            sclReply = ""

            if timeout > 0.0:
                try:
                    data = await asyncio.wait_for(areader.read(4096), timeout)
                    recStr = data.decode()
                    sclReply = recStr[2:-1]
                except:
                    self.writer.close()
                    await self.writer.wait_closed()
                    raise OsuActorError(f"Failed to read the data")
                    return False, sclReply
            else:
                raise OsuActorError(f"Wrong timeout!")
                return False, sclReply

            if len(sclReply) > 0:
                if sclReply[:4] == 'DONE':
                    return True, sclReply
                if sclReply[:3] == 'ERR':
                    return True, sclReply
                if sclReply[:2] == 'IS':
                    return True, sclReply



    async def getWAGOEnv(self):

        rtdAddr = 8

        rtdKeys = ['rtd1(40009)',
                   'rtd2(40010)',
                   'rtd3(40011)',
                   'rtd4(40012)']
        numRTDs = len(rtdKeys)

        rhtRHKeys = ['rhtRH1(40002)',
                     'rhtRH2(40004)',
                     'rhtRH3(40006)']
        rhtTKeys = ['rhtT1(40001)',
                    'rhtT2(40003)',
                    'rhtT3(40005)']
        numRHT = len(rhtTKeys)
        rhtAddr = 8

        RH0 = 0.0
        RHs = 100.0/32767.0
        T0 = -30.0
        Ts = RHs
 
        wagoClient = ModbusClient(self.host)

#        self.loop, wagoClient = await ModbusClient(schedulers.ASYNC_IO, host = self.host, loop=self.loop)
        
        if not wagoClient.connect():
            raise OsuActorError(f"Cannot connect to WAGO at %s" %(self.host))
            return False
        
        try:
            rd = wagoClient.read_holding_registers(rtdAddr, numRTDs)
            for i in range(4):
                self.sensors[rtdKeys[i]] = round(ptRTD2C(float(rd.registers[i])), 2)
        except:
            raise OsuActorError(f"Failed to have the rtd data")
            return False
        # Read the E+E RH/T sensors and convert to physical units.

        try:
            rd = wagoClient.read_holding_registers(rhtAddr,2*numRHT)
            for i in range(3):
                self.sensors[rhtRHKeys[i]] = round(RH0 + RHs*float(rd.registers[2*i]), 2)
                self.sensors[rhtTKeys[i]] = round(T0 + Ts*float(rd.registers[2*i+1]), 2)
        except:
            raise OsuActorError(f"Failed to have the rht data")
            return False
        
        wagoClient.close()
        return True

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

def parse_IS(reply: bytes):

    match = re.search(b"\x00\x07IS=([0-1])([0-1])[0-1]{6}\r$", reply)
    if match is None:
        return False

    if match.groups() == (b"1", b"0"):
        return "open"
    elif match.groups() == (b"0", b"1"):
        return "closed"
    else:
        return False

