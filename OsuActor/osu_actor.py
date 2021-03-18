import asyncio
import OSU_control as osu

from clu import AMQPActor, command_parser

desi=osu.Controller()
desi.controller_status['exp_shutter_power'] = 'ON'
#desi.controller_status['exp_shutter_seal'] = 'DEFLATED'


@command_parser.command()
async def open(command):
    """Open the shutter."""

    command.info(text="Opening the shutter!")
    # Here we would implement the actual communication
    #desi=osu.Controller()
    #print(desi.controller_status)
    #desi.controller_status['exp_shutter_power'] = 'ON'
    #print(desi.controller_status)
    desi.controller_status['exp_shutter_seal'] = 'DEFLATED'
    desi.exp_shutter('open')

    #print(desi.controller_status)
    # with the shutter hardware.
    command.finish(shutter="open")

    return


@command_parser.command()
async def close(command):
    """Close the shutter."""

    command.info(text="Closing the shutter!")
    # Here we would implement the actual communication
    #desi=osu.Controller()
    #print(desi.controller_status)
    #desi.controller_status['exp_shutter_power'] = 'ON'
    #print(desi.controller_status)
    desi.controller_status['exp_shutter_seal'] = 'DEFLATED'
    desi.exp_shutter('close')
    # with the shutter hardware.
    command.finish(shutter="closed")

    return


class OsuActor(AMQPActor):
    def __init__(self):
            super().__init__(
            name="osu_actor",
            user="guest",
            password="guest",
            host="localhost",
            port=5672,
            version="0.1.0",
        )


async def run_actor():
    actor = await OsuActor().start()
    await actor.run_forever()


asyncio.run(run_actor())

