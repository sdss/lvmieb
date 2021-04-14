#from osuactor.controller.controller import OsuController

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: shutter.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


#We will not use this code no more. Please use this code just for reference _CK

"""
import asyncio
import OSU_control as osu

from pymodbus3.client.sync import ModbusTcpClient as mbc
from clu import AMQPActor, command_parser

desi=osu.Controller()
desi.controller_status['exp_shutter_power'] = 'ON'
#desi.controller_status['exp_shutter_seal'] = 'DEFLATED'


@command_parser.command()
async def open(command):

    command.info(text="Opening the shutter!")
    # Here we would implement the actual communication
    #desi=osu.Controller()
    #print(desi.controller_status)
    #desi.controller_status['exp_shutter_power'] = 'ON'
    #print(desi.controller_status)
    desi.controller_status['exp_shutter_seal'] = 'DEFLATED'
    desi.exp_shutter('open')

    #print(desi.controller_status)
    # with the shutter hardware.
    command.finish(shutter="open")

    return


@command_parser.command()
async def close(command):

    command.info(text="Closing the shutter!")
    # Here we would implement the actual communication
    #desi=osu.Controller()
    #print(desi.controller_status)
    #desi.controller_status['exp_shutter_power'] = 'ON'
    #print(desi.controller_status)
    desi.controller_status['exp_shutter_seal'] = 'DEFLATED'
    desi.exp_shutter('close')
    # with the shutter hardware.
    command.finish(shutter="closed")

    return
"""
