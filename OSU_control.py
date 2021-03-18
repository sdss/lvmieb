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

SkipNIR = False	# temp flag to skip NIR initialization when not present

# Time until motor controller is ready to run commands after powered on
SclPowerSleep = 15.

# Device List used by motor controller communication code
devList = ["exp_shutter","hartmann_left","hartmann_right"]
shutterList = devList[1] 
doorList = devList[2:] 

# This list is used by the WAGO power control utilities
powList = ['exp_shutter_power', 
            'hartmann_left_power', 
            'hartmann_right_power']

# Device Addresses
devAddr = {"exp_shutter":("10.7.45.27",7776),
           "hartmann_left"    :("10.7.45.27",7777),
           "hartmann_right"   :("10.7.45.27",7778)}

devSock = {}
devConnected = {"exp_shutter":False,"hartmann_left":False,"hartmann_right":False}

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

# Hartmann Doors (both left and right have same commands, but
# individual status bit tables)

hdCmds = {"init":"QX1","home":"QX2","open":"QX3","close":"QX4","status":"IS"}
leftStat = [['unused','unused'],
            ['unused','unused'],
            ['unused','unused'],
            ['unused','unused'],
            ['unused','unused'],
            ['unused','unused'],
            ['CLOSED','OPEN'],
            ['OPEN','CLOSED']]
rightStat = [['unused','unused'],
             ['unused','unused'],
             ['unused','unused'],
             ['unused','unused'],
             ['unused','unused'],
             ['unused','unused'],
             ['OPEN','CLOSED'],
             ['CLOSED','OPEN']]

# Combine all the status tables into a single device dictionary

statusBits = {'exp_shutter':expStat,
              'hartmann_left':leftStat,'hartmann_right':rightStat}

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
            'hartmann_left' : 'ERROR', 		# ERROR | OPEN | CLOSED
            'hartmann_left_power' : 'ERROR', 	# ERROR | ON | OFF
            'hartmann_right' : 'ERROR', 	# ERROR | OPEN | CLOSED
            'hartmann_right_power' : 'ERROR', 	# ERROR | ON | OFF
            'wago' : 'ERROR',			# ERROR | READY 
            'exp_shutter' : 'ERROR',		# ERROR | OPEN | CLOSED
            'exp_shutter_seal' : 'ERROR',	# ERROR | INFLATED | DEFLATED
            'exp_shutter_power' : 'ERROR',	# ERROR | ON | OFF
            'illuminator' : 'ERROR',	# ERROR | READY | NOTREADY | ON | OFF | FLASH
            'updated' : datetime.datetime.utcnow().isoformat()
          } 
        self.exposure_status = {
            'status' : 'NOTREADY', 		# READY | NOTREADY | EXPOSING
            'actual' : 0., 			# Actual time (returned) 
            'exptime' : 0., 			# Requested time 
            'updated' : datetime.datetime.utcnow().isoformat()
          } 
        self.sensors = {
            '40001' : -273., 
            '40002' : -1., 
            '40003' : -273., 
            '40004' : -1., 
            '40005' : -273., 		# IEB internal temp
            '40006' : -1.,
            'updated' : datetime.datetime.utcnow().isoformat()
          } 
        # some variables for the exposure logic
        self._use_callback = True                       # Whether or not to use expose callback at end of cycle
        self._stop_exposure = threading.Event()         # Flag to stop exposure
        self._mechanism_lock = threading.RLock()
        self._exposure_lock = threading.RLock()
        self.flasher_enabled = threading.Event()
        self.flasher_enabled.clear()

    def initialize(self): 
        """ 
        Initialize the controller to the default state, which is the 
        same as ready to take an exposure: 
          - Exposure shutter on, closed, with seal deflated
          - Hartmann Doors are open, or **assumed** open if they are off 
        Initialize also populates the humidity and temperature sensors
        Note: WAGO status == 'ERROR' does not preclude operations. 
        """ 

        # Check to see if an exposure is in progress
        if self.exposure_status['status'] == 'EXPOSING': 
            raise RuntimeError("ERROR in initialize(): Exposure in progress") 

        # Populate the self.sensors data structure 
        wago_status1, reply = self.getWAGOEnv()
        if wago_status1: 
            print("WAGO sensor values read") 
     
        # Populate self.controller_status data structure power values
        wago_status2, reply = self.getWAGOPower()
        if wago_status2: 
            print("WAGO power values read") 
    
        # If both previous steps returned True, set WAGO status to ready 
        if wago_status1 and wago_status2: 
            self.controller_status['wago'] = 'READY' 
        else: 
            print("ERROR: Did not read WAGO sensors/powers") 
     
        # Initialize the Doors if ON, otherwise assume they are OPEN
        for door in doorList: 
            if self.controller_status[door+'_power'] == 'OFF': 
                self.controller_status[door] = 'OPEN' 
                print("Power off for %s, assumed open" % door) 
            else: 
                status, reply = SclCmd(door, 'open') 
                self.SclStatusUpdate(door) 
                # Home it if out of position (Home position is OPEN) 
                if reply == 'ERR1' or reply == 'ERR2': 
                    status, reply = SclCmd(door, 'home') 
                    time.sleep(1.)
                    self.SclStatusUpdate(door) 
                    if status == False: 
                        print("Error: %s door failed to initialize" % door) 
                    else: 
                        print("Door %s initialized after home sequence" % door) 
                else: 
                    print("Door %s initialized" % door) 
    
        # Initialize the Shutters
        #if SkipNIR: 
        #    shutterList = ['exp_shutter'] 
        for shutter in shutterList: 
            if self.controller_status[shutter+'_power'] != 'ON': 
                print(" Warning: %s not on, turning it on" % shutter) 
                #status, reply = self.power(shutter, 'on') 
                self.power(shutter, 'on') 
                self.SclStatusUpdate(shutter) 
                if shutter == 'exp_shutter' and self.controller_status['exp_shutter'] != 'CLOSED': 
                  self.exp_shutter('close') 
            if self.controller_status[shutter+'_power'] != 'ON': 
                print("ERROR: %s not on" % shutter) 
            else: 
                self.SclStatusUpdate(shutter) 
                # If shutter is status is ERROR, home the shutter
                # If seal is inflated, deflate
                # If exp_shutter is open, close it
                if shutter == 'exp_shutter': 
                    if self.controller_status[shutter] == 'ERROR': 
                        status, reply = SclCmd(shutter, 'home') 
                    if self.controller_status[shutter] == 'OPEN': 
                        #status, reply = SclCmd(shutter, 'close') 
                        self.exp_shutter('close') 
                    if self.controller_status[shutter+'_seal'] == 'INFLATED': 
                        #status, reply = SclCmd(shutter, 'deflate') 
                        self.seal(shutter, 'deflate') 
                self.SclStatusUpdate(shutter) 
            if self.controller_status[shutter] == 'ERROR': 
                print("Error with shutter %s initialization" % shutter) 
            else: 
                print("Shutter %s initialized" % shutter) 

        # Update illuminator status: 
        if self._check_illuminator_readiness():
            self.controller_status['illuminator'] = 'OFF'
        else: 
            self.controller_status['illuminator'] = 'NOTREADY'
 
        # Set status to 'READY' if: 
        #  1) power for both shutters is ON
        #  2) both hartmann doors are OPEN
        #  3) exp_shutter is closed
        #  4) both seals are deflated 
        #  5) wago is READY 
        if self.controller_status['exp_shutter_power'] == 'ON' and self.controller_status['hartmann_left'] == 'OPEN' and self.controller_status['hartmann_right'] == 'OPEN' and self.controller_status['exp_shutter'] == 'CLOSED' and self.controller_status['exp_shutter_seal'] == 'DEFLATED' and self.controller_status['wago'] == 'READY': 
            self.controller_status['status'] = 'READY' 
        else: 
            print("Error with initialization, status set to ERROR") 
        self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
 
        # Update exposure status: 
        self._check_exposure_readiness()

# Methods used by DOS

    def get(self, what): 
        """ 
        Returns information about the spectrograph controller, current state
        'what' is the name of the requested quantity
        """ 
        if what == 'status':
            return dict(self.controller_status)
        elif what == 'sensors':
            # update sensor readings
            self.getWAGOEnv() 
            return dict(self.sensors)
        elif what.startswith('exposure'):
            return dict(self.exposure_status)
        elif what == 'unit':
            return self.unit
        elif what =='controller_status':
            return 'READY'
        else:
            return 'FAILED: Invalid option'

    def illuminator(self, action='off', duty_cycle=0.5, flashtime=0.05, callback = None, **callback_args): 
        """
        Controls the fiber illuminator. 
        action = 'on', 'off', 'flash'
        duty_cycle: fraction of the time the LED is on. Must be [0.,1.]
        flashtime: LED on time per flash (>minflash). Units are seconds. 
        If action = 'on' or 'flash', returns error if 
            _check_illuminator_readiness() is FALSE
        If action = 'on', turns on illuminator and leaves it on continuously.
        If action = 'flash', flashes the illuminator continuously with 
          some duty_cycle of flashes, each flash of length flashtime 
        If action = 'off', turns off illuminator. This includes stopping 
          the continuous flash thread.
        """

        minflash = 0.02 # minimum flash time 

        if action == 'on':
            if self._check_illuminator_readiness():    
                if self.controller_status['illuminator'] == 'ON': 
                    print(" Warning: illuminator already on") 
                if self.controller_status['illuminator'] == 'FLASH': 
                    raise RuntimeError("ERROR illuminator flash sequence in progress") 
                self.controller_status['illuminator'] = 'ON'
                status, reply = SclCmd('exp_shutter', 'on') 
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
            else: 
                self.controller_status['illuminator'] = 'NOTREADY'
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                raise RuntimeError("ERROR in illuminator(): Not ready") 

        if action == 'flash': 
            if self._check_illuminator_readiness():    
                if self.controller_status['illuminator'] == 'OFF': 
                    raise RuntimeError("ERROR illuminator must be on to initiate a flash sequence") 
                elif self.controller_status['illuminator'] == 'FLASH': 
                    raise RuntimeError("ERROR illuminator flash sequence in progress") 
                elif duty_cycle < 0. or duty_cycle > 1.:
                    raise RuntimeError("ERROR duty_cycle not in range [0,1]") 
                elif flashtime < minflash: 
                    raise RuntimeError("ERROR flashtime must be >= 0.02 seconds ") 
                elif duty_cycle == 1.: 
                    # Just turn it on (no thread)
                    self.controller_status['illuminator'] = 'ON'
                    status, reply = SclCmd('exp_shutter', 'on') 
                    self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                else: 
                    self.flasher_enabled.set()
                    self.controller_status['illuminator'] = 'FLASH'
                    
                    self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                    flasher_thread = threading.Thread(name = 'flash_thread', target = self._flasher, args=(flashtime, duty_cycle) )
                    flasher_thread.daemon = True
                    flasher_thread.start()
            else: 
                self.controller_status['illuminator'] = 'NOTREADY'
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                raise RuntimeError("ERROR in illuminator(): Not ready") 
        if action == 'off': 
            self.flasher_enabled.clear()
            status, reply = SclCmd('exp_shutter', 'off') 
            self.controller_status['illuminator'] = 'OFF'
            self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()

    def _flasher(self, flashtime, duty_cycle):
        # flashtime is the time the illuminator is on per cycle in seconds
        # duty cycle is the fraction of the cycle the illuminator is on
        overhead = 0.007 # measured value [Jan 2020] 
        maxon = flashtime/(flashtime+overhead)
        if duty_cycle>maxon:
            duty_cycle = maxon
        toff = flashtime/duty_cycle - flashtime - overhead
        while self.flasher_enabled.is_set():
            self.flash_off()
            time.sleep(toff)
            if self.flasher_enabled.is_set():  # see if turned off
                self.flash_on()
                time.sleep(flashtime)

####################################################################
#
# Exposure control (mostly a copy from spectro_simulator.py) 
#
####################################################################

    def expose(self, action, exptime, callback = None, **callback_args):
        """
        The expose command checks that the spectrograph is ready for an 
        exposure by verifying that the exposure shutter is closed, 
        the illuminator is off, and the seals are deflated. 
        The routine also checks that the mechanisms are powered.
        If given, a callback function is registered. This function will be 
        called when the exposure shutter closes. callback_args are passed to 
        that function (for example an exposure number). For example:
            expose('normal',15.0,callback=myfunction,id=15,msg='this will be send to the callback function')
        when the shutter closes (or stop is called with use_callback == True, 
        the callback function will be called with both id and msg as named 
        arguments. It is recommended to use the standard *args, **kwargs
        syntax for the callback function.
        The routine returns once the exposure has started.
        The exposure time is kept by the NUC
        The status in the exposure status dictionary is set to EXPOSING
        Inputs:
            action:  normal/dark
            exposure_time:  exposure time in seconds. If set to None the shutter remains open until closed
            callback: function to be called when shutter closes
            callback_args: arguments passed to the callback function
        Returns:
            exposure status dictionary
        """

        if self.exposure_status['status'] == 'EXPOSING': # Raise an exception if we are already exposing
            raise RuntimeError('Already exposing. Stop onging exposure first before starting a new exposure.')
        if self.controller_status['illuminator'] == 'ON':
            raise RuntimeError("Cannot start exposure: Illuminator is on")
        # check power status
        if (self.controller_status["exp_shutter_power"] == "OFF"):
            raise RuntimeError("Cannot run exposure: Exposure shutter power off")
        if not (action == 'normal' or action == 'dark'):
            raise ValueError("'%s' is not a valid action" %(action))
        # Check shutter configuration
        if (self.controller_status["exp_shutter"] != "CLOSED"):
            raise RuntimeError("Exposure shutter has to be closed to start expose command.")
        if self.controller_status['exp_shutter_seal'] !='DEFLATED':
            raise RuntimeError("Seals need to be deflatedfor expose command.")
        # Exposure time
        if exptime == None:
            exposure_time = None
        else:
            exposure_time = float(exptime)    # throws an exception if invalid type
            if exposure_time < 0.0:
                raise ValueError("Exposure time cannot be negative.")
        with self._mechanism_lock:
            self._stop_exposure.clear()
            # Prevent duplicate arguments
            if 'exptime' in callback_args:
                del callback_args['exptime']
            self._check_exposure_readiness()
            self._check_illuminator_readiness()
            if callback != None:
                self._use_callback = True
            exposure_thread = threading.Thread(name = 'expose_thread', target = self._expose_thread, args = ( action, exposure_time, callback), kwargs= callback_args,)
            exposure_thread.setDaemon(True)
            exposure_thread.start()
        return dict(self.controller_status)

    def _expose_thread(self, action, exptime, callback, **callback_args):
        """
        The expose_thread executes the exposure and manages the 
        exposure time
        """
        with self._exposure_lock:
            self.exposure_status["status"] = "EXPOSING"
            self.exposure_status['actual'] = 0
            self.exposure_status['exptime'] = exptime
            self.exposure_status['updated'] = datetime.datetime.utcnow().isoformat() 

        self._check_illuminator_readiness()
        if (action == 'normal'):
            with self._mechanism_lock:
                self.exp_shutter('open')
        start_time = time.time()
        self._update_exposure(start_time, exptime)
        if exptime is None:    # keep shutter open until close. Update exposure status dictionary
            while not self._stop_exposure.isSet():
                time.sleep(.1)
                self._update_exposure(start_time, exptime)
        else:
            end = time.time() + exptime
            while not self._stop_exposure.isSet():
                if (time.time() >= end):   # Done exposing?
                    self._update_exposure(start_time, exptime)
                    break
                else:     # No
                    self._update_exposure(start_time, exptime)
                    time.sleep(.1)
        with self._exposure_lock:
            self.exposure_status["status"] = "READY"
            self.exposure_status['updated'] = datetime.datetime.utcnow().isoformat()
        with self._mechanism_lock:
            self.exp_shutter('close')
        self._check_exposure_readiness()
        self._check_illuminator_readiness()
        self._stop_exposure.clear()
        if (callback is not None and self._use_callback):
            callback(**callback_args)
            
    def stop(self, use_callback = False):
        """
        Stop an exposure
        """
        if type(use_callback) is not bool:
            raise ValueError("'%s' is not a valid value for 'use_callback'"%(use_callback))
        if self.exposure_status['status'] != 'EXPOSING':
            raise RuntimeError("No exposure to stop")
        self._use_callback = use_callback
        self._stop_exposure.set()
        return dict(self.controller_status)

    def prepare_for_exposure(self):
        """
        Prepare for an exposure
        The routine will check that both shutters are powered, the exposure 
        shutter is closed, and both seals are 
        deflated. 
        """
        if self.exposure_status['status'] == 'EXPOSING':
            raise RuntimeError("Cannot prepare for exposure: Exposure is occurring")
        with self._mechanism_lock:
            # self.illuminator('off') 	# don't need to do this
            if self.controller_status['exp_shutter'] != 'CLOSED': 
                self.exp_shutter("close")
            if self.controller_status['exp_shutter_seal'] != 'DEFLATED': 
                self.seal("exp_shutter", "deflate")
        self._check_exposure_readiness()
        self._check_illuminator_readiness()
        return dict(self.exposure_status)

#################################################################
#
#  Utility and helper functions
#
#################################################################
    
    def _update_exposure(self, start_time, exptime):
        self.exposure_status['actual'] = round(time.time() - start_time,3)
        self.exposure_status['exptime'] = exptime
        self.exposure_status['updated'] = datetime.datetime.utcnow().isoformat()

    def _check_exposure_readiness(self):
        """ 
        Check if we are ready for an exposure
        All of these conditions have to be met for the exposure status to be READY:
            illuminator off
            exp shutter powered
            exp shutter closed
            exp shutter seal deflated
            and no ongoing exposure
        Sets the status in exposure_status to READY or NOTREADY
        Returns False is not ready (or already exposing)
        """
        if self.exposure_status['status'] == 'EXPOSING':
            return False
        with self._mechanism_lock:
            if self.controller_status['illuminator'] != 'ON' and \
                self.controller_status['exp_shutter_power'] == 'ON' and \
                self.controller_status['exp_shutter'] == 'CLOSED' and \
                self.controller_status['exp_shutter_seal'] == 'DEFLATED':
                with self._exposure_lock:
                    self.exposure_status['status'] = 'READY'
                return True
            else:
                with self._exposure_lock:
                    self.exposure_status['status'] = 'NOTREADY'
                return False

    def _check_illuminator_readiness(self):
        """ 
        Check if the illuminator is ready
        All of these conditions have to be met for the exposure status to be READY:
            exp shutter powered
            exp shutter closed
            seals inflated
            status is READY
            and no ongoing exposure
        Sets the illuminator status in to NOTREADY or /READY/ON/OFF
        Returns False is not ready
        """
        if self.exposure_status['status'] == 'EXPOSING':
            with self._mechanism_lock:
                self.controller_status['illuminator'] = 'NOTREADY'
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
            return False
        with self._mechanism_lock:
            if self.controller_status['status'] == 'READY' and \
                self.controller_status['exp_shutter_power'] == 'ON' and \
                self.controller_status['exp_shutter'] == 'CLOSED' and \
                self.controller_status['exp_shutter_seal'] == 'INFLATED':
                if self.controller_status['illuminator'] not in ['ON', 'OFF', 'FLASH', 'READY']:
                    #self.controller_status['illuminator'] = 'READY'
                    self.controller_status['illuminator'] = 'OFF'
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                return True
            else:
                self.controller_status['illuminator'] = 'NOTREADY'
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                return False
                
#################################################################
#
#  Low-level methods that interact with the motor controllers 
#
#################################################################

    def power(self, device, action): 
        """  
        Power 'device' on or off and update controller_status 
        device = [exp_shutter, hartmann_left, hartmann_right] 
        action = [on, off] 
        Notes: 
         - A command to power off the Hartmann Doors will open them first
         - A command to power off the shutters will close them first
         - Does not check the exposure status 
        """  
    
        # Check for a valid device, convert to 'power' dictionary entry 
        if device in devList: 
            powdev = device+"_power" 
        else: 
            raise RuntimeError("ERROR in power(): %s not in %s" % (device, devList))
      
        # Check for valid action 
        if action.upper() == 'ON': 
            command = 'ON' 
        elif action.upper() == 'OFF': 
            command = 'OFF'
        else: 
            raise RuntimeError("ERROR in power(): %s not one of [on, off]" % action) 
       
        # If command powers off a Hartmann door, open it first if it isn't open
        if device == 'hartmann_left' and command == 'OFF' and self.controller_status['hartmann_left'] != 'OPEN': 
            self.hartmann('left', 'open') 
    
        if device == 'hartmann_right' and command == 'OFF' and self.controller_status['hartmann_right'] != 'OPEN': 
            self.hartmann('right', 'open') 

        # If a command powers off a shutter, close it first and make sure 
        # the seal status is set to deflated (seal deflates on power off
        if device == 'exp_shutter' and command == 'OFF' and self.controller_status['exp_shutter'] == 'OPEN': 
            self.exp_shutter('close') 
        
        if device == 'exp_shutter' and command == 'OFF': 
            self.controller_status['exp_shutter_seal'] = 'DEFLATED'

        # Communicate power command to WAGO 
        # Only send ON command if motor controller was OFF, as this 
        #   takes some time. Run a status update after power up.  
        if command == 'ON' and self.controller_status[powdev] == 'OFF': 
            status, reply = self.setWAGOPower(powdev, command)
            print(" Warning: %s was not ON, takes %.0f seconds to be ready" % (powdev, SclPowerSleep))  
            time.sleep(SclPowerSleep) 	# Time to wake up 
            status, reply = self.SclStatusUpdate(device)
            self.controller_status[powdev] = 'ON'
            # Update exposure status: 
            status = self._check_exposure_readiness()
            if status == 'False':  
                self.controller_status[powdev] = 'ERROR'
                raise RuntimeError("ERROR with power(%s, %s)" % (device, command))
            #return status, reply
            self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
            return dict(self.controller_status)
        else:  # command is OFF, always okay to send as returns quickly 
            status, reply = self.setWAGOPower(powdev, command)
            if status == 'False':  
                self.controller_status[powdev] = 'ERROR'
                raise RuntimeError("ERROR with power(%s, %s)" % (device, command))
            #return status, reply
            self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
            return dict(self.controller_status)

    def seal(self, shutter, action): 
        """  
        Inflate or deflate the seal of the named shutter
        shutter = [exp_shutter] 
        action = [inflate, deflate] 
        NOTE: This does not check exposure state 
        """  
     
        # Check for valid device
        if shutter in shutterList: 
            dev = shutter
        else: 
            raise RuntimeError("ERROR in seal(): %s not in %s" % (shutter, shutterList))

        # Check for valid action 
        if action == 'inflate': 
            command = 'inflate' 
        elif action == 'deflate': 
            command = 'deflate'
        else: 
            raise RuntimeError("ERROR in seal(): %s not one of [inflate, deflate]" % action) 
    
        # Check that the shutter is powered on, return error if powered off 
        if self.controller_status[shutter+'_power'] != 'ON': 
            raise RuntimeError("ERROR in seal(): %s status is OFF" % shutter) 
       
        # Check that the shutter is closed, return error if open and 
        # command is to inflate the seal 
        if self.controller_status[shutter] != 'CLOSED' and command == 'inflate': 
            raise RuntimeError("ERROR in seal(): %s status is OPEN" % shutter) 
    
        # Operate the seal 
        status, sclReply = SclCmd(dev, command) 
    
        # Check the reply, update the data structure
        if command == 'inflate':
            if sclReply == 'DONE': 
                self.controller_status[dev+'_seal'] = 'INFLATED' 
            elif sclReply == 'ERR1': 
                raise RuntimeError("ERROR %s in seal() with command %s to %s: shutter is open" % (sclReply, command, dev) )
            else: 
                raise RuntimeError("ERROR %s in seal() with command %s to %s" % (sclReply, command, dev) )
                self.controller_status[dev+'_seal'] = 'ERROR' 

        if command == 'deflate':
            if sclReply == 'DONE': 
                self.controller_status[dev+'_seal'] = 'DEFLATED' 
            else: 
                raise RuntimeError("ERROR %s in seal() with command %s to %s" % (sclReply, command, dev) )
                self.controller_status[dev+'_seal'] = 'ERROR' 

        # Update illuminator status: 
        if self._check_illuminator_readiness():
            self.controller_status['illuminator'] = 'OFF'
        else: 
            self.controller_status['illuminator'] = 'NOTREADY'

        # Update exposure status: 
        status = self._check_exposure_readiness()
        self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
        return dict(self.controller_status)

    def hartmann(self, door, position): 
        """  
        Operate one or both hartmann doors 
        door = [left, right, both] 
        position = [open, close] 
        """  
    
        BothDoors = False 
        # Check for valid device
        if door == 'left': 
            dev = 'hartmann_left' 
        elif door == 'right': 
            dev = 'hartmann_right' 
        elif door == 'both': 
            BothDoors = True
            dev = 'hartmann_left' 
        else: 
            raise RuntimeError("ERROR in hartmann(): %s not one of [left, right, both]" % door) 
    
        # Check for valid position
        if position == 'open': 
            command = 'open' 
        elif position == 'close': 
            command = 'close'
        else: 
            raise RuntimeError("ERROR in hartmann(): %s not one of [open, close]" % position) 
    
        # Check that the door(s) are powered on
        if BothDoors: 
            if self.controller_status['hartmann_left_power'] != 'ON': 
                raise RuntimeError("ERROR in hartmann(): hartmann_left_power OFF or ERROR") 
            if self.controller_status['hartmann_right_power'] != 'ON': 
                raise RuntimeError("ERROR in hartmann(): hartmann_right_power OFF or ERROR" ) 
        else: 
            if self.controller_status[dev+'_power'] != 'ON': 
                raise RuntimeError("ERROR in hartmann(): %s_power OFF or ERROR " % dev) 
    
        # Operate the door(s) 
        if BothDoors: 
            leftstatus, leftreply = SclCmd('hartmann_left', command) 
            rightstatus, rightreply = SclCmd('hartmann_right', command) 
        elif dev == 'hartmann_left': 
            status, leftreply = SclCmd(dev, command) 
        elif dev == 'hartmann_right': 
            status, rightreply = SclCmd(dev, command) 
         
        # Check the reply, update the data structure
        if BothDoors: 
            # Check left side reply -- 
            dev = 'hartmann_left'
            if leftreply == 'DONE': 
                if command == 'open':
                    self.controller_status['hartmann_left'] = 'OPEN' 
                elif command == 'close': 
                    self.controller_status['hartmann_left'] = 'CLOSED' 
            else: 
                self.controller_status['hartmann_left'] = 'ERROR' 
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                raise RuntimeError("ERROR %s in hartmann(): %s may be ajar" % (leftreply, dev) )
            # Check right side reply -- 
            dev = 'hartmann_right'
            if rightreply == 'DONE': 
                if command == 'open':
                    self.controller_status['hartmann_right'] = 'OPEN' 
                elif command == 'close': 
                    self.controller_status['hartmann_right'] = 'CLOSED' 
            else: 
                self.controller_status['hartmann_right'] = 'ERROR' 
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                raise RuntimeError("ERROR %s in hartmann(): %s may be ajar" % (rightreply, dev) )
        elif door == 'left': 
            if leftreply == 'DONE': 
                if command == 'open':
                    self.controller_status['hartmann_left'] = 'OPEN' 
                elif command == 'close': 
                    self.controller_status['hartmann_left'] = 'CLOSED' 
            else: 
                self.controller_status['hartmann_left'] = 'ERROR'
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                raise RuntimeError("ERROR %s in hartmann(): %s may be ajar" % (leftreply, dev) )
        elif door == 'right':  
            if rightreply == 'DONE': 
                if command == 'open':
                    self.controller_status['hartmann_right'] = 'OPEN' 
                elif command == 'close': 
                    self.controller_status['hartmann_right'] = 'CLOSED' 
            else: 
                self.controller_status['hartmann_right'] = 'ERROR' 
                self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
                raise RuntimeError("ERROR %s in hartmann(): %s may be ajar" % (rightreply, dev) )
        else: 
            raise RuntimeError("Error in hartmann()") 

        self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
        return dict(self.controller_status)

    def exp_shutter(self, position): 
        """  
        Operate the exposure shutter. Check the motor is on, the seal is 
        deflated, illuminator is off, and then move to the target position. 
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
    
        # Check the EXP seal status
        if self.controller_status['exp_shutter_seal'] != 'DEFLATED': 
            raise RuntimeError("ERROR in exp_shutter(): exp_shutter seal status %s" % self.controller_status['exp_shutter_seal']) 
    
        # Operate the shutter
        status, sclReply = SclCmd('exp_shutter', command) 
    
        if command == 'open':
            if sclReply == 'DONE': 
                self.controller_status['exp_shutter'] = 'OPEN' 
            else: 	# if fails, pause briefly and try one more time
                time.sleep(0.25) 
                self.SclStatusUpdate('exp_shutter') 
                if self.controller_status['exp_shutter'] == 'ERROR':  
                  raise RuntimeError("ERROR in exp_shutter(): %s with command %s" % (sclReply, command) ) 
        elif command == 'close':
            if sclReply == 'DONE': 
                self.controller_status['exp_shutter'] = 'CLOSED' 
            else: 
                time.sleep(0.25) 
                self.SclStatusUpdate('exp_shutter') 
                if self.controller_status['exp_shutter'] == 'ERROR':  
                  raise RuntimeError("ERROR in exp_shutter(): %s with command %s" % (sclReply, command) ) 
        else: 
            raise RuntimeError("ERROR in exp_shutter()") 

        # Update exposure status: 
        status = self._check_exposure_readiness()
        self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
        return dict(self.controller_status)

    def flash_off(self): 
        """
        Disengage the solid state relay and turn off the illuminator
        Note that this does not also disengage the mechanical relay
        This should only be used for fast cycling of the illuminator, the 
        mechanical relay should also be shut off to turn the illuminator 
        completely off. 
        """ 
        if self._check_illuminator_readiness():
            if self.controller_status['illuminator'] == 'FLASH' or self.controller_status['illuminator'] == 'ON': 
                status, sclReply = SclCmd('exp_shutter', 'ssroff') 
            else: 
                RuntimeError("ERROR in flash_off(): illuminator must be on or in flash mode") 
        else: 
            raise RuntimeError("ERROR in flash_off(): illuminator not ready") 


    def flash_on(self): 
        """
        Engage the solid state relay and turn on the illuminator
        Note that this does not also engage the mechanical relay
        This should only be used for fast cycling of the illuminator. 
        The mechanical relay should already be on.
        """ 
        if self._check_illuminator_readiness():
            if self.controller_status['illuminator'] == 'FLASH' or self.controller_status['illuminator'] == 'ON': 
                status, sclReply = SclCmd('exp_shutter', 'ssron') 
            else: 
                print("ERROR in flash_on(): illuminator must be on or in flash mode") 
        else: 
            raise RuntimeError("ERROR in flash_on(): illuminator not ready") 

    def SclStatusUpdate(self, device): 
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
        status, sclReply = SclCmd(device, 'status') 
    
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
        
            self.controller_status['illuminator'] = 'OFF' 
            if bitVal[1] == 0: 
                self.controller_status['illuminator'] = 'ON' 
        
            self.controller_status['exp_shutter_seal'] = 'DEFLATED' 
            if bitVal[0]: 
                self.controller_status['exp_shutter_seal'] = 'INFLATED' 
      
        if device == 'hartmann_left': 
            self.controller_status['hartmann_left'] = 'ERROR'
            if bitVal[6]==bitVal[7]:	# Door is ajar
                self.controller_status['hartmann_left'] = 'ERROR'
            elif bitVal[6] == 1 and bitVal[7] == 0: 
                self.controller_status['hartmann_left'] = 'OPEN' 
            elif bitVal[6] == 0 and bitVal[7] == 1: 
                self.controller_status['hartmann_left'] = 'CLOSED' 
             
        if device == 'hartmann_right': 
            self.controller_status['hartmann_right'] = 'ERROR'
            if bitVal[6]==bitVal[7]:	# Door is ajar
                self.controller_status['hartmann_right'] = 'ERROR'
            elif bitVal[6] == 1 and bitVal[7] == 0: 
                self.controller_status['hartmann_right'] = 'CLOSED' 
            elif bitVal[6] == 0 and bitVal[7] == 1: 
                self.controller_status['hartmann_right'] = 'OPEN' 
    
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
  
    def getWAGOEnv(self):
  
        # WAGO register addresses and associated datum keywords in the
        # "sensors" dictionary
    
        # The E+E RH/Temp sensors are connected to an 8-port analog
        # input module on the WAGO modbus at address 40001 (logical
        # address 0).  Each sensor is connected to two adjacent ports:
        # RH then T.
  
        rhtAddr = 0
        rhtRHKeys = ['40004',
                       '40002']
        rhtTKeys  = ['40003',
                       '40001']
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
        rtdKeys = ['40005',
                   '40006']
        numRTDs = len(rtdKeys)
    
        # Get a WAGO client handle and connect (port 502 is implicit
        # as per the modbus spec).
    
        wagoClient = mbc(self.wagoHost)
        if not wagoClient.connect():
            return False,"** ERROR: Cannot connect to WAGO at %s" % (self.wagoHost)
    
        # Read the Pt RTD Temperature Sensors
    
        rd = wagoClient.read_holding_registers(rtdAddr,numRTDs)
        for i in range(numRTDs):
            self.sensors[rtdKeys[i]] = round(ptRTD2C(float(rd.registers[i])), 2) 

    
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
  
    def getWAGOPower(self):
  
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
# setWAGOPower(self,dev,state)
#
# Set a WAGO power control state of the named device.
#
# Inputs:
#   dev = name of a DESI device
#   state = state to set, "on" or "off"
#
# Sets the appropriate entry in the self.controller_status
# dictionary with the state achieved "on" or "off"
#
# This function is invoked internally by the power() method
#
# Returns:
#   (status,msgStr)
# where:
#   status = True on success, with msgStr = DONE
#   status = False on errors, with msgStr containing a fault message
#
# See also: getWAGOPower()
#
#---------------------------------------------------------------------------
  
    def setWAGOPower(self,dev,state):
  
        # 8-port digital output register address
    
        do8Addr = 512
        maxPorts = 8
    
        # Mapping between 8DO ports and Desi devices
    
        numDevs = len(powList)
    
        # Validate input parameters
    
        if not dev in powList:
            return False,"Unknown device '%s'" % (dev)
    
        if not state in ['ON','OFF']:
            return False,"Unknown power state '%s', must be ON or OFF" % (state)
    
        # Get a WAGO client handle and connect (port 502 is implicit as
        # per modbus spec).
    
        wagoClient = mbc(self.wagoHost)
        if not wagoClient.connect():
            return False,"** ERROR: Cannot connect to WAGO at %s" % (self.wagoHost)
        idev = powList.index(dev)
 
        # relay open == Hartmann Doors powered off
        if dev == 'hartmann_left_power' or dev == 'hartmann_right_power': 
          if state == 'ON':
              reqState = True  # output off, relay opens, power ON
          else:
              reqState = False   # output on, relay closes, power OFF

        # relay open == shutters powered on 
        if dev == 'exp_shutter_power': 
          if state == 'ON':
              reqState = False  # output off, relay closes, power ON
          else:
              reqState = True   # output on, relay opens, power OFF
    
        # Set the output state reqested
    
        rd = wagoClient.write_coil(idev,reqState)
        sleep(0.1) # required pause before reading...
    
        # Now read the ports to confirm
    
        #rd = wagoClient.read_holding_registers(do8addr,maxPorts)
        rd = wagoClient.read_holding_registers(do8Addr,maxPorts)
        outState = wagoDOReg(rd.registers[0],numOut=maxPorts)
    
        # Changed due to change in HD logic [PM|26Jan2018] 
        for i in range(numDevs):
            if i == 0 or i == 1:  # shutters 
                if outState[i]: 
                    self.controller_status[powList[i]] = "OFF"
                else:
                    self.controller_status[powList[i]] = "ON"
            if i == 2 or i == 3:  # doors 
                if outState[i]:
                    self.controller_status[powList[i]] = "ON"
                else:
                    self.controller_status[powList[i]] = "OFF"
    
        # All done, clean up and return success
        self.controller_status['updated'] = datetime.datetime.utcnow().isoformat()
    
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

##################################################################
# Low-level routines 
##################################################################


def SclCmd(dev, command, SelectTimeout=0.5):
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
    elif dev == 'hartmann_left' or 'hartmann_right':
      if command in hdCmds == False:
        return False, "Error: %s is not a valid %s command" % (command, dev)
      else:
        sclCmd = hdCmds[command]
    else: 
      return False, "Error: %s and %s combination not found" % (command, dev)
  
    # Tweak timeouts
    if command == 'inflate' or command == 'deflate':
      SelectTimeout = 2.5
    if command == 'status':
      SelectTimeout = 1.
    if dev == 'hartmann_left' or dev == 'hartmann_right': 
      if command == 'open' or command == 'close' or command == 'home': 
        SelectTimeout = 4.
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
  
    status, reply = sendSclCmd(reqDev, sclCmd)
  
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

def sendSclCmd(dev,cmdStr):

    if dev not in devList:
        return False,"ERROR: Invalid device %s requested" % (dev)

    if not devConnected[dev]:
        return False,"ERROR: %s is not connected" % (dev)

    # Header and tail for the eSCL command packet

    sclHead = chr(0)+chr(7)
    sclTail = chr(13)

    # build the command packet

    sclStr = str2scl(cmdStr)

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

def str2scl(cmdStr):
    sclHead = chr(0)+chr(7)
    sclTail = chr(13)
    sclStr = sclHead + cmdStr.upper() + sclTail  # build the packet
    return sclStr


