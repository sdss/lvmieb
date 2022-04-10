import asyncio

from clu.command import Command

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import LvmIebError

from . import parser


@parser.command()
async def labtemp(command: Command, controllers: dict[str, IebController]):
    """

    Args:


    Returns:
        [type]: command.finish()
    """

    tasks = []

    for lab in controllers:
        if controllers[lab].name == "sensor":
            print("in here")
            try:
                tasks.append(controllers[lab].labstatus())

            except LvmIebError as err:
                return command.fail(error=str(err))

    lab_dict = await asyncio.gather(*tasks)
    print(lab_dict[0])
    if lab_dict[0]:
        command.info(lab_dict[0])
    return command.finish()
