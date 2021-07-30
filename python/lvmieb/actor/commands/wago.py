# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong YANG, Taeeun Kim
# @Date: 2021-03-22
# @Filename: telemetry.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations, print_function, division, absolute_import
from clu.command import Command

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import LvmIebError

from . import parser


@parser.group()
def wago(*args):
    """control the wago IOModule."""
    pass


@wago.command()
async def status(command: Command, controllers: dict[str, IebController]):
    """Returns the status of wago sensor."""
    for wago in controllers:
        if controllers[wago].name == 'wago':
            try:
                wago_status1 = await controllers[wago].getWAGOEnv()
                if wago_status1:
                    return command.finish(
                        rhtT1=controllers[wago].sensors['rhtT1(40001)'],
                        rhtRH1=controllers[wago].sensors['rhtRH1(40002)'],
                        rhtT2=controllers[wago].sensors['rhtT2(40003)'],
                        rhtRH2=controllers[wago].sensors['rhtRH2(40004)'],
                        rtd1=controllers[wago].sensors['rtd1(40009)'],
                        rtd2=controllers[wago].sensors['rtd2(40010)'],
                        rtd3=controllers[wago].sensors['rtd3(40011)'],
                        rtd4=controllers[wago].sensors['rtd4(40012)'])
                else:
                    return command.fail(text="ERROR: Did not read sensors/powers")
            except LvmIebError as err:
                return command.fail(error=str(err))
    return command.finish()


@wago.command()
async def getpower(command: Command, controllers: dict[str, IebController]):
    """Returns the status of wago sensor."""
    for wago in controllers:
        if controllers[wago].name == 'wago':
            try:
                wago_status1 = await controllers[wago].getWAGOPower()
                if wago_status1:
                    return command.finish(
                        shutter_power=controllers[wago].power["shutter_power"],
                        hartmann_right_power=controllers[wago].power["hartmann_right_power"],
                        hartmann_left_power=controllers[wago].power["hartmann_left_power"])
                else:
                    return command.fail(text="ERROR: Did not read sensors/powers")
            except LvmIebError as err:
                return command.fail(error=str(err))
    return command.finish()


@wago.command()
async def setpower(command: Command, controllers: dict[str, IebController]):
    """Returns the status of wago sensor."""
    for wago in controllers:
        if controllers[wago].name == 'wago':
            try:
                wago_status1 = await controllers[wago].setWAGOPower("hartmann_right_power", 'ON')
                if wago_status1:
                    command.finish(
                        shutter_power=controllers[wago].power["shutter_power"],
                        hartmann_right_power=controllers[wago].power["hartmann_right_power"],
                        hartmann_left_power=controllers[wago].power["hartmann_left_power"])
                else:
                    return command.fail(text="ERROR: Did not read sensors/powers")
            except LvmIebError as err:
                return command.fail(error=str(err))
    return command.finish()
