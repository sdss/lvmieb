from __future__ import absolute_import, annotations, division, print_function

from clu.command import Command

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import LvmIebError
import click
from . import parser
import asyncio

CCDLIST = ["r1", "b1", "z1"]


@parser.group()
def transducer(*args):
    """control the wago IOModule."""
    pass


@transducer.command()
async def status(command: Command, controllers: dict[str, IebController]):
    """Returns the status of transducer."""
    
    tasks = []
    pres_result = {}
    
    for pres in controllers:
        if controllers[pres].spec == "sp1":
            if controllers[pres].name in CCDLIST:
                try:
                    tasks.append(controllers[pres].read_temp(controllers[pres].name))                
                    tasks.append(controllers[pres].read_pressure(controllers[pres].name))
                except LvmIebError as err:
                    return command.fail(error=str(err))

    pres_list = await asyncio.gather(*tasks)
    
    for i in pres_list:
        pres_result.update(i)
    
    try:
        return command.finish(
            r1_pressure=pres_result["r1_pressure"],
            b1_pressure=pres_result["b1_pressure"],
            z1_pressure=pres_result["z1_pressure"],
            r1_temperature=pres_result["r1_temperature"],
            b1_temperature=pres_result["b1_temperature"],
            z1_temperature=pres_result["z1_temperature"],
        )
    except LvmIebError as err:
        return command.fail(error=str(err))
    command.finish()
    return