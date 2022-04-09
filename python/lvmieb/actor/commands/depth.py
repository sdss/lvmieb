import asyncio

import click
from clu.command import Command

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import LvmIebError

from . import parser


@parser.group()
def depth(*args):
    """control the linear gauge depth."""
    pass


@depth.command()
@click.argument(
    "spectro",
    type=click.Choice(["sp1", "sp2", "sp3"]),
    default="sp1",
    required=False,
)
@click.argument(
    "ccd",
    type=click.Choice(["r1", "b1", "z1"]),
    default="z1",
    required=False,
)
async def status(
    command: Command, controllers: dict[str, IebController], spectro: str, ccd: str
):
    """Returns the status of transducer."""
    tasks = []
    for depth in controllers:
        if controllers[depth].spec == spectro:
            if controllers[depth].name == "sp1":
                try:
                    tasks.append(controllers[depth].read_depth_probes())

                except LvmIebError as err:
                    return command.fail(error=str(err))

    depth = await asyncio.gather(*tasks)
    print(depth)

    try:
        command.info({spectro: {ccd: depth[0]}})
    except LvmIebError as err:
        return command.fail(error=str(err))
    return command.finish()
