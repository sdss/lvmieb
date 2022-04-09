import asyncio

from clu.command import Command

from lvmieb.controller.controller import IebController

from . import parser


@parser.command()
async def labtemp(command: Command, controllers: dict[str, IebController]):
    """

    Args:


    Returns:
        [type]: command.finish()
    """

    reader, writer = await asyncio.wait_for(
        asyncio.open_connection("10.7.45.30", 1111),
        timeout=2,
    )
    writer.write(b"status\n")
    await writer.drain()

    data = await asyncio.wait_for(reader.readline(), timeout=1)
    print(data)
    lines = data.decode().strip().splitlines()

    writer.close()
    await writer.wait_closed()

    temp = hum = last = None
    for line in lines:
        name, temp, hum, __, last = line.split()
        if name == "H5179":
            break

    if temp is None or hum is None or last is None:
        labtemp = -999
        labhum = -1
        # raise ValueError("Did not get a measurement for H5179.")

    labtemp = round(float(temp), 2)
    labhum = round(float(hum), 2)
    command.info({"labtemp": labtemp, "labhum": labhum})
    return command.finish()
