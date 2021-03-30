#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: expose.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

"""

import asyncio
import OSU_control as osu

from pymodbus3.client.sync import ModbusTcpClient as mbc
from clu import AMQPActor, command_parser

desi=osu.Controller()
desi.controller_status['exp_shutter_power'] = 'ON'
#desi.controller_status['exp_shutter_seal'] = 'DEFLATED'

@command_parser.command()
async def telemetry(command):

    wago_status2, reply = desi.getWAGOPower()
    wago_status1, reply = desi.getWAGOEnv()
    if wago_status1 and wago_status2:
        command.info(text="Temperature & Humidity is:",status={
                "rhtT1(40001)":desi.sensors['40001'],
                "rhtRH1(40002)":desi.sensors['40002'],
                "rhtT2(40003)":desi.sensors['40003'],
                "rhtRH2(40004)":desi.sensors['40004'],
                "rhtT3(40005)":desi.sensors['40005'],
                "rhtRH3(40006)":desi.sensors['40006'],
                "rtd1(40009)":desi.sensors['40009'],
                "rtd2(40010)":desi.sensors['40010'],
                "rtd3(40011)":desi.sensors['40011'],
                "rtd4(40012)":desi.sensors['40012']
                })
        wagoClient = mbc(desi.wagoHost)
        rd = wagoClient.read_holding_registers(0,12)
        print(rd.registers)

    else:
        return command.fail(text=f"ERROR: Did not read sensors/powers")

    return command.finish()

"""
