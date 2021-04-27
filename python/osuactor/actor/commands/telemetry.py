#We have to change this code to interact with controller.py _CK
#Please refer to open.py and close.py

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-03-22
# @Filename: expose.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


#added by CK 2021/03/30                                                                                                                                                                                                     
from __future__ import annotations

import asyncio

from clu.command import Command

from osuactor.controller.controller import OsuController
from osuactor.exceptions import OsuActorError

from . import parser

@parser.command()
async def telemetry(command: Command, controllers: dict[str, OsuController]):

    for shutter in controllers:
        if controllers[shutter].name == 'shutter':
            try:
                wago_status1 = await controllers[shutter].getWAGOEnv()
                if wago_status1:
                    command.info(text="Temperature & Humidity is:",status={
                "rhtT1(40001)":controllers[shutter].sensors['rhtT1(40001)'],
                "rhtRH1(40002)":controllers[shutter].sensors['rhtRH1(40002)'],
                "rhtT2(40003)":controllers[shutter].sensors['rhtT2(40003)'],
                "rhtRH2(40004)":controllers[shutter].sensors['rhtRH2(40004)'],
                "rhtT3(40005)":controllers[shutter].sensors['rhtT3(40005)'],
                "rhtRH3(40006)":controllers[shutter].sensors['rhtRH3(40006)'],
                "rtd1(40009)":controllers[shutter].sensors['rtd1(40009)'],
                "rtd2(40010)":controllers[shutter].sensors['rtd2(40010)'],
                "rtd3(40011)":controllers[shutter].sensors['rtd3(40011)'],
                "rtd4(40012)":controllers[shutter].sensors['rtd4(40012)']
                })
                else:
                    return command.fail(text=f"ERROR: Did not read sensors/powers")
            except OsuActorError as err:
                return command.fail(error=str(err))

    return command.finish()
