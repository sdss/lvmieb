import asyncio
import OSU_control as osu

from pymodbus3.client.sync import ModbusTcpClient as mbc
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

@command_parser.command()
async def telemetry(command):

    wago_status2, reply = desi.getWAGOPower()
    wago_status1, reply = desi.getWAGOEnv()
    if wago_status1 and wago_status2:
        command.info(text="Temperature & Humidity is:",status={
                "rhtT1(40001)":desi.sensors['40001'],
                "rhtRH1(40002)":desi.sensors['40002'],
                "rhtT2(40003)":desi.sensors['40003'],
                "rhtRH2(40004)":desi.sensors['40004'],
                "rhtT3(40005)":desi.sensors['40005'],
                "rhtRH3(40006)":desi.sensors['40006'],
                "rtd1(40009)":desi.sensors['40009'],
                "rtd2(40010)":desi.sensors['40010'],
                "rtd3(40011)":desi.sensors['40011'],
                "rtd4(40012)":desi.sensors['40012']
                })
        wagoClient = mbc(desi.wagoHost)
        rd = wagoClient.read_holding_registers(0,12)
        print(rd.registers)

    else:
        return command.fail(text=f"ERROR: Did not read sensors/powers")

    return command.finish()


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
#    acor = await OsuActor().stop()
    actor = await OsuActor().start()
    await actor.run_forever()
#    await actor.stop()

asyncio.run(run_actor())

