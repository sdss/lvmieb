# -*- coding: utf-8 -*-
#

from __future__ import annotations, print_function, division, absolute_import

import warnings
import asyncio
import re
import datetime
from lvmieb.exceptions import LvmIebError, LvmIebWarning
from pymodbus.client.asynchronous.async_io import AsyncioModbusTcpClient as ModbusClient


__all__ = ["IebController"]

# Device list

devList = ["shutter", "hartmann_left", "hartmann_right"]


# Exposure shutter commands
expCmds = {"init": "QX1", "home": "QX2", "open": "QX3", "close": "QX4",
           "flash": "QX5", "on": "QX8", "off": "QX9",
           "ssroff": "QX10", "ssron": "QX11", "status": "IS"}

# Hartmann Door commands
hdCmds = {"init": "QX1", "home": "QX2", "open": "QX3", "close": "QX4", "status": "IS"}

# This list is used by the WAGO power control utilities
powList = ['shutter_power',
           'unused',
           'hartmann_left_power',
           'hartmann_right_power']


class IebController:
    """
            Talks to an Ieb controller over TCP/IP
    """
    count = 0

    def __init__(self, host: str, port: int, name: str = ""):
        self.name = name
        self.sensors = {
            'rhtT1(40001)': -273., 		# Temperatures in C
            'rhtRH1(40002)': -1., 	# Humidity in percent
            'rhtT2(40003)': -273.,
            'rhtRH2(40004)': -1.,
            'rtd1(40009)': -273., 		# IEB internal temp
            'rtd2(40010)': -273.,		# Bench temp near NIR camera
            'rtd3(40011)': -273., 		# Bench temp near collimator
            'rtd4(40012)': -273.} 		# Bench temp near cryostats
        self.power_status = {
            'hartmann_left_power': 'ERROR',   # ERROR | ON | OFF
            'hartmann_right_power': 'ERROR',  # ERROR | ON | OFF
            'shutter_power': 'ERROR'          # ERROR | ON | OFF
        }
        self.wagohost = '10.7.45.28'
        self.wagoport = 502
        self.__status_event = asyncio.Event()
        self.reader = None
        self.writer = None
        self.hartmann_right_status = None
        self.hartmann_left_status = None
        self.shutter_status = None
        self.lock = asyncio.Lock()
        self.host = host
        self.port = port

    async def initialize(self):
        r, w = await asyncio.open_connection(self.host, self.port)
        # parse the low-level command to the hardware
        message = 'QX1'
        SelectTimeout = 1
        sclHead = chr(0) + chr(7)
        sclTail = chr(13)
        sclStr = sclHead + message.upper() + sclTail
        try:
            w.write(sclStr.encode())
            await w.drain()
        except LvmIebError as err:
            w.close()
            await w.wait_close()
            warnings.warn(str(err), LvmIebWarning)
        # read byte stream from the motor controller
        try:
            reply = await asyncio.wait_for(r.readuntil(b"\r"), SelectTimeout)
            print(reply)
        except LvmIebError as err:
            w.close()
            await w.wait_closed()
            warnings.warn(str(err), LvmIebWarning)
        try:
            w.close()
            await w.wait_closed()
        except LvmIebError as err:
            warnings.warn(str(err), LvmIebWarning)

    async def send_command(self, command, SelectTimeout=3.0):
        async with self.lock:
            current_time = datetime.datetime.now()
            print('host: %s when send command              : %s', self.port, current_time)
            # check that the device exists
            if self.name in devList is False:
                raise LvmIebError("%s is not a valid device" % self.name)
            # check that the command is legal for the device
            if self.name == "shutter":
                if command in expCmds is False:
                    raise LvmIebError("%s is not a valid %s command" % (command, self.name))
                else:
                    c_message = expCmds[command]
            elif self.name == "hartmann_left" or self.name == "hartmann_right":
                if command in hdCmds is False:
                    raise LvmIebError("%s is not a valid %s command" % (command, self.name))
                else:
                    c_message = hdCmds[command]
            else:
                raise LvmIebError("%s and %s combination not found" % (command, self.name))
            # get the status from the hardware
            if command != 'status':
                try:
                    if self.name == 'shutter':
                        self.shutter_status = await self.get_status()
                    elif self.name == 'hartmann_right':
                        self.hartmann_right_status = await self.get_status()
                    elif self.name == 'hartmann_left':
                        self.hartmann_left_status = await self.get_status()
                except LvmIebError as err:
                    raise LvmIebError("Could not connect the %s" % self.name)
            # check the shutter& harmann door status before open and close
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
                        raise LvmIebError(
                            f"The hartmann right door is already {self.hartmann_right_status}!"
                            )
                elif command == 'close':
                    if self.hartmann_right_status == "closed":
                        raise LvmIebError(
                            f"The hartmann right door is already {self.hartmann_right_status}!"
                            )
            elif self.name == "hartmann_left":
                if command == "open":
                    if self.hartmann_left_status == "opened":
                        raise LvmIebError(
                            f"The hartmann left door is already {self.hartmann_left_status}!"
                            )
                elif command == "close":
                    if self.hartmann_left_status == "closed":
                        raise LvmIebError(
                            f"The hartmann left door is already {self.hartmann_left_status}!"
                            )
            # Tweak timeouts
            if self.name == "hartmann_left" or self.name == "hartmann_right":
                if command == "open" or command == "close" or command == "home":
                    SelectTimeout = 4.0
            if self.name == "shutter":
                if command == "home":
                    SelectTimeout = 4.0

            # connection
            current_time = datetime.datetime.now()
            print('host: %s before connection              : %s', self.port, current_time)
            self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
            current_time = datetime.datetime.now()
            print('host: %s after connection               : %s', self.port, current_time)

            # parse the low-level command to the hardware
            sclHead = chr(0)+chr(7)
            sclTail = chr(13)
            sclStr = sclHead + c_message.upper() + sclTail

            try:
                current_time = datetime.datetime.now()
                print('host: %s before write command           : %s', self.port, current_time)
                self.writer.write(sclStr.encode())
                current_time = datetime.datetime.now()
                print('host: %s after write command            : %s', self.port, current_time)
                await self.writer.drain()
                current_time = datetime.datetime.now()
                print('host: %s after write drain              : %s', self.port, current_time)
            except LvmIebError as err:
                self.writer.close()
                await self.writer.wait_close()
                raise LvmIebError("Failed to write the data")

            # read byte stream from the motor controller
            try:
                current_time = datetime.datetime.now()
                print('host: %s before readuntil               : %s', self.port, current_time)
                if command == "status" or command == "init" or command == "home":
                    reply = await asyncio.wait_for(self.reader.readuntil(b"\r"), SelectTimeout)
                elif command == "open" or command == "close":
                    reply = await asyncio.wait_for(self.reader.readuntil(b"DONE\r"), SelectTimeout)
                current_time = datetime.datetime.now()
                print('host: %s after readuntil                : %s', self.port, current_time)
            except LvmIebError as err:
                self.writer.close()
                await self.writer.wait_closed()
                raise LvmIebError("failed to read the data")

            # disconnect device
            try:
                current_time = datetime.datetime.now()
                print('host : %s before close writer            : %s', self.port, current_time)
                self.writer.close()
                await self.writer.wait_closed()
                current_time = datetime.datetime.now()
                print('host : %s after close writer             : %s', self.port, current_time)
            except LvmIebError("Could not disconnect the %s" % self.name) as err:
                warnings.warn(str(err), LvmIebWarning)

            print(reply)
            
            if command == "status":
                if self.name == "shutter":
                    assert isinstance(reply, bytes)
                    shutter_stat = parse_IS(self.name, reply)
                    self.shutter_status = shutter_stat
                    return shutter_stat
                elif self.name == "hartmann_left":
                    assert isinstance(reply, bytes)
                    hartmann_stat = parse_IS(self.name, reply)
                    self.hartmann_left_status = hartmann_stat
                    return hartmann_stat
                elif self.name == "hartmann_right":
                    assert isinstance(reply, bytes)
                    hartmann_stat = parse_IS(self.name, reply)
                    self.hartmann_right_status = hartmann_stat
                    return hartmann_stat
            else:
                if b"DONE" in reply:
                    # updating the status of each hardware
                    print("%s done is replied", self.port)
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
                    print("%s error is replied", self.port)
                    # send to home
                    await self.set_home()
                    raise LvmIebError("Error in the controller, please check the hardware")

    async def get_status(self):
        print(self.host, self.port)
        r, w = await asyncio.open_connection(self.host, self.port)
        # parse the low-level command to the hardware
        message = 'IS'
        SelectTimeout = 1
        sclHead = chr(0) + chr(7)
        sclTail = chr(13)
        sclStr = sclHead + message.upper() + sclTail
        try:
            w.write(sclStr.encode())
            await w.drain()
        except LvmIebError as err:
            w.close()
            await w.wait_close()
            raise LvmIebError("Failed to write the data")
        # read byte stream from the motor controller
        try:
            reply = await asyncio.wait_for(r.readuntil(b"\r"), SelectTimeout)
            print(reply)
        except LvmIebError as err:
            w.close()
            await w.wait_closed()
            raise LvmIebError("failed to read the data")
        try:
            w.close()
            await w.wait_closed()
        except LvmIebError as err:
            raise LvmIebError("Could not disconnect the %s" % self.name)
        if message == "IS" and reply:
            assert isinstance(reply, bytes)
            stat = parse_IS(self.name, reply)
            print(stat)
            if stat == "error":
                print("error occured.. setting to home")
                await self.set_home()
            return stat

    async def set_home(self):
        r, w = await asyncio.open_connection(self.host, self.port)
        # parse the low-level command to the hardware
        message = 'QX2'
        SelectTimeout = 1
        sclHead = chr(0) + chr(7)
        sclTail = chr(13)
        sclStr = sclHead + message.upper() + sclTail
        try:
            w.write(sclStr.encode())
            await w.drain()
        except LvmIebError as err:
            w.close()
            await w.wait_close()
            raise LvmIebError("Failed to write the data")
        # read byte stream from the motor controller
        try:
            reply = await asyncio.wait_for(r.readuntil(b"\r"), SelectTimeout)
            print(reply)
        except LvmIebError as err:
            w.close()
            await w.wait_closed()
            raise LvmIebError("failed to read the data")
        try:
            w.close()
            await w.wait_closed()
        except LvmIebError as err:
            raise LvmIebError("Could not disconnect the %s" % self.name)

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
        RHs = 100.0 / 32767.0
        T0 = -30.0
        Ts = RHs
        wagoClient = ModbusClient(self.wagohost, self.wagoport)
        await wagoClient.connect()
        rd = await wagoClient.protocol.read_holding_registers(rtdAddr, numRTDs)
        for i in range(4):
            self.sensors[rtdKeys[i]] = round(ptRTD2C(float(rd.registers[i])), 2)
        rd = await wagoClient.protocol.read_holding_registers(rhtAddr, 2 * numRHT)
        for i in range(2):
            self.sensors[rhtRHKeys[i]] = round(RH0 + RHs * float(rd.registers[2 * i]), 2)
            self.sensors[rhtTKeys[i]] = round(T0 + Ts * float(rd.registers[2 * i + 1]), 2)
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
        wagoClient = ModbusClient(self.wagohost, self.wagoport)
        await wagoClient.connect()
        rd = await wagoClient.protocol.read_holding_registers(do8Addr, maxPorts)
        outState = wagoDOReg(rd.registers[0], numOut=maxPorts)
        for i in range(numDevs):
            if i == 0 or i == 1:  # shutters
                if outState[i]:
                    self.power_status[powList[i]] = "OFF"
                else:
                    self.power_status[powList[i]] = "ON"
            if i == 2 or i == 3:  # shutters
                if outState[i]:
                    self.power_status[powList[i]] = "ON"
                else:
                    self.power_status[powList[i]] = "OFF"
        wagoClient.protocol.close()
        return True, 'DONE'

    async def setWAGOPower(self, dev, state):
        # 8-port digital output register address
        do8Addr = 512
        maxPorts = 8
        # Mapping between 8DO ports and Desi devices
        numDevs = len(powList)
        # Validate input parameters
        print(dev)
        print(state)
        if dev not in powList:
            return False, "Unknown device '%s'" % (dev)
        if state not in ['ON', 'OFF']:
            return False, "Unknown power state '%s', must be ON or OFF" % (state)
        # Get a WAGO client handle and connect (port 502 is implicit as
        # per modbus spec).
        wagoClient = ModbusClient(self.wagohost, self.wagoport)
        await wagoClient.connect()
        idev = powList.index(dev)
        # relay open is Hartmann Doors powered off
        if dev == 'hartmann_left_power' or dev == 'hartmann_right_power':
            if state == 'ON':
                reqState = True  # output off, relay opens, power ON
            else:
                reqState = False   # output on, relay closes, power OFF
        # relay open is shutters powered on
        if dev == 'shutter_power': 
            if state == 'ON':
                reqState = False  # output off, relay closes, power ON
            else:
                reqState = True   # output on, relay opens, power OFF
        # Set the output state reqested
        print(f'idev is {idev}')
        print(f'reqState is {reqState}')
        rd = await wagoClient.protocol.write_coil(idev, reqState)
        # Now read the ports to confirm
        rd = await wagoClient.protocol.read_holding_registers(do8Addr, maxPorts)
        outState = wagoDOReg(rd.registers[0], numOut=maxPorts)
        print(f'out state is {outState}')
        # Changed due to change in HD logic [PM|26Jan2018] 
        for i in range(numDevs):
            if i == 0 or i == 1:  # shutters 
                if outState[i]:
                    self.power_status[powList[i]] = "OFF"
                else:
                    self.power_status[powList[i]] = "ON"
            if i == 2 or i == 3:  # doors
                if outState[i]:
                    self.power_status[powList[i]] = "ON"
                else:
                    self.power_status[powList[i]] = "OFF"    
        # All done, clean up and return success        
        wagoClient.protocol.close()
        return True, 'DONE'


def ptRTD2C(rawRTD):
    tempRes = 0.1     # module resolution is 0.1C per ADU
    tempMax = 850.0   # maximum temperature for a Pt RTD in deg C
    wrapT = tempRes * ((2.0**16) - 1) # ADU wrap at <0C to 2^16-1
    temp = tempRes * rawRTD
    if temp > tempMax:
        temp -= wrapT
    return temp


def wagoDOReg(rd, numOut=8):
    testOut = []
    for i in range(numOut):
        testOut.append((rd & 2**i) is 2**i)
    return testOut


# low level command to parse the byte stream from the motor controller
def parse_IS(name, reply: bytes):
    match = re.search(b"\x00\x07IS=([0-1])([0-1])[0-1]{6}\r$", reply)
    if match is None:
        return False
    # for hartmann_left, 01 was opened, and 10 is closed
    if name == "hartmann_right" or name == "shutter":
        if match.groups() == (b"1", b"0"):
            return "opened"
        elif match.groups() == (b"0", b"1"):
            return "closed"
        else:
            return "error"
    else:
        if match.groups() == (b"0", b"1"):
            return "opened"
        elif match.groups() == (b"1", b"0"):
            return "closed"
        else:
            return "error"
