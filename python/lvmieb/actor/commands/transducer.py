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

    pres_result = {}

    camera_order = []
    pres_list = []
    error = False

    NRETRIES = 3
    for iretry in range(NRETRIES):
        camera_order = []
        tasks = []
        pres_list = []
        error = False

        for controller_name in controllers:
            if spectro is not None and controller_name != spectro:
                continue
            controller = controllers[controller_name]
            for camera, pressure_transducer in controller.pressure.items():
                tasks.append(pressure_transducer.read_pressure())
                tasks.append(pressure_transducer.read_temperature())
                camera_order.append(camera)

        for task in tasks:
            try:
                # We avoid doing this with a gather to prevent multiple connections to
                # the device at the same time.
                result = await task
                pres_list.append(result)
            except Exception as err:
                error = err
                break

        if error is not False and iretry < NRETRIES - 1:
            command.warning(f"Failed getting pressure status: {error}. Retrying.")
            continue
        else:
            break

    if len(pres_list) == 0 or error:
        return command.fail(error="Unable to retrieve any pressure data.")

    for ii, camera in enumerate(camera_order):
        camera_results = pres_list[2 * ii : 2 * ii + 2]
        for jj, measurement in enumerate(["pressure", "temperature"]):
            camera_result = camera_results[jj]
            pres_result[f"{camera}_{measurement}"] = camera_result

    command.finish(transducer=pres_result)
