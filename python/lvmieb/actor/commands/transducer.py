from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import click

from . import parser


if TYPE_CHECKING:
    from lvmieb.actor.actor import ControllersType, IEBCommand


@parser.group()
def transducer(*args):
    """Reports pressure transducer values.."""
    pass


@transducer.command()
@click.argument("spectro", type=click.Choice(["sp1", "sp2", "sp3"]), required=False)
async def status(
    command: IEBCommand,
    controllers: ControllersType,
    spectro: str | None = None,
):
    """Returns the status of transducer."""

    tasks = []

    pres_result = {}
    camera_order = []

    for controller_name in controllers:
        if spectro is not None and controller_name != spectro:
            continue
        controller = controllers[controller_name]
        for camera, pressure_transducer in controller.pressure.items():
            tasks.append(pressure_transducer.read_pressure())
            tasks.append(pressure_transducer.read_temperature())
            camera_order.append(camera)

    pres_list = await asyncio.gather(*tasks, return_exceptions=True)

    for ii, camera in enumerate(camera_order):
        camera_results = pres_list[2 * ii : 2 * ii + 2]
        for jj, measurement in enumerate(["pressure", "temperature"]):
            camera_result = camera_results[jj]
            if isinstance(camera_result, Exception):
                command.warning(f"Failed getting {camera} {measurement}.")
                camera_result = -999.0
            pres_result[f"{camera}_{measurement}"] = camera_result

    command.finish(transducer=pres_result)
