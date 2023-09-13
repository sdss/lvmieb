from __future__ import annotations

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

    pres_list = []

    NRETRIES = 3
    for iretry in range(NRETRIES):
        pres_list = []
        for task in tasks:
            try:
                # We avoid doing this with a gather to prevent multiple connections to
                # the device at the same time.
                result = await task
                pres_list.append(result)
            except Exception as err:
                if iretry < NRETRIES - 1:
                    command.warning(f"Failed getting pressure status: {err}. Retrying.")
                    continue
        break

    for ii, camera in enumerate(camera_order):
        camera_results = pres_list[2 * ii : 2 * ii + 2]
        for jj, measurement in enumerate(["pressure", "temperature"]):
            camera_result = camera_results[jj]
            if camera_result is False or isinstance(camera_result, Exception):
                command.warning(f"Failed getting {camera} {measurement}.")
                camera_result = -999.0
            pres_result[f"{camera}_{measurement}"] = camera_result

    command.finish(transducer=pres_result)
