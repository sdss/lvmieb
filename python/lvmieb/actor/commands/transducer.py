from __future__ import annotations

from typing import TYPE_CHECKING

import click
import numpy

from . import parser


if TYPE_CHECKING:
    from lvmieb.actor.actor import ControllersType, IEBCommand
    from lvmieb.controller.controller import IEBController


async def read_transducer(
    controller: IEBController,
    camera: str,
    measurement: str = "pressure",
):
    """Reads a pressure transducer value."""

    NRETRIES = 3

    pressure_transducer = controller.pressure[camera]

    if measurement == "pressure":
        func = pressure_transducer.read_pressure
    elif measurement == "temperature":
        func = pressure_transducer.read_temperature
    else:
        raise ValueError(f"Unknown measurement {measurement}")

    for iretry in range(NRETRIES):
        try:
            result = await func()
            return result
        except Exception as err:
            if iretry < NRETRIES - 1:
                continue
            else:
                raise err


@parser.group()
def transducer(*args):
    """Reports pressure transducer values.."""
    pass


@transducer.command()
@click.argument("spectro", type=str, required=False)
async def status(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Returns the status of transducer."""

    pres_result = {}

    for controller_name in controllers:
        if spectro is not None and controller_name != spectro:
            continue

        controller = controllers[controller_name]

        # We read cameras and measurements sequentially instead of with a gather
        # to avoid too many concurrent accesses to the hardware. This could not matter
        # that much anymore, though.
        for cam in controller.pressure:
            for measurement in ["pressure", "temperature"]:
                try:
                    value = await read_transducer(controller, cam, measurement)
                except Exception as err:
                    command.warning(f"Failed to read {measurement} from {cam}: {err}")
                    value = numpy.nan

                pres_result[f"{cam}_{measurement}"] = value

    command.finish(transducer=pres_result)
