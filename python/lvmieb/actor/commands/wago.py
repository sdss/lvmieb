# -*- coding: utf-8 -*-
#
# @Author: Changgon Kim, Mingyeong YANG, Taeeun Kim
# @Date: 2021-03-22
# @Filename: telemetry.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import absolute_import, annotations, division, print_function

from clu.command import Command

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import LvmIebError
import click
from . import parser


@parser.group()
def wago(*args):
    """control the wago IOModule."""
    pass


@wago.command()
async def status(command: Command, controllers: dict[str, IebController]):
    """Returns the status of wago sensor."""
    
    for sp1 in controllers:
        if controllers[sp1].name == "sp1":
            try:
                wago_status1 = await controllers[sp1].getWAGOEnv()
                if wago_status1:
                    return command.finish(
                        rhtRH1=controllers[sp1].sensors["rhtRH1(40001)"],
                        rhtT1=controllers[sp1].sensors["rhtT1(40002)"],
                        rhtRH2=controllers[sp1].sensors["rhtRH2(40003)"],
                        rhtT2=controllers[sp1].sensors["rhtT2(40004)"],
                        rhtRH3=controllers[sp1].sensors["rhtRH3(40005)"],
                        rhtT3=controllers[sp1].sensors["rhtT3(40006)"],
                        rtd1=controllers[sp1].sensors["rtd1(40009)"],
                        rtd2=controllers[sp1].sensors["rtd2(40010)"],
                        rtd3=controllers[sp1].sensors["rtd3(40011)"],
                        rtd4=controllers[sp1].sensors["rtd4(40012)"],
                    )
                else:
                    return command.fail(text="ERROR: Did not read sensors/powers")
            except LvmIebError as err:
                return command.fail(error=str(err))
    return command.finish()


@wago.command()
async def getpower(command: Command, controllers: dict[str, IebController]):
    """Returns the status of wago sensor."""
    for sp1 in controllers:
        if controllers[sp1].name == "sp1":
            try:
                wago_status1 = await controllers[sp1].getWAGOPower()
                if wago_status1:
                    return command.finish(
                        shutter_power=controllers[sp1].power["shutter_power"],
                        hartmann_right_power=controllers[sp1].power[
                            "hartmann_right_power"
                        ],
                        hartmann_left_power=controllers[sp1].power[
                            "hartmann_left_power"
                        ],
                    )
                else:
                    return command.fail(text="ERROR: Did not read sensors/powers")
            except LvmIebError as err:
                return command.fail(error=str(err))
    return command.finish()


@wago.command()
@click.argument(
    "DEVICE",
    type=click.Choice(["shutter", "hartmann_left", "hartmann_right"]),
)
@click.option(
    "--on",
    "action",
    flag_value="ON",
    required=True,
    help="Turn on device",
)
@click.option(
    "--off",
    "action",
    flag_value="OFF",
    required=True,
    help="Turn off device",
)
async def setpower(command: Command, controllers: dict[str, IebController], device: str, action: str):
    """Returns the status of wago sensor."""
    device_string = device + "_power"
    for sp1 in controllers:
        if controllers[sp1].name == "sp1":
            try:
                wago_status1 = await controllers[sp1].setWAGOPower(
                    device_string, action
                )
                if wago_status1:
                    command.finish(
                        shutter_power=controllers[sp1].power["shutter_power"],
                        hartmann_right_power=controllers[sp1].power[
                            "hartmann_right_power"
                        ],
                        hartmann_left_power=controllers[sp1].power[
                            "hartmann_left_power"
                        ],
                    )
                else:
                    return command.fail(text="ERROR: Did not read sensors/powers")
            except LvmIebError as err:
                return command.fail(error=str(err))
    return
