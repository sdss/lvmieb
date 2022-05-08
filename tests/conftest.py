# encoding: utf-8
#
# conftest.py

"""
Here you can add fixtures that will be used for all the tests in this
directory. You can also add conftest.py files in underlying subdirectories.
Those conftest.py will only be applies to the tests in that subdirectory and
underlying directories. See https://docs.pytest.org/en/2.7.3/plugins.html for
more information.
"""
import asyncio
import os
import re

import pytest as pytest

import clu.testing
from clu.actor import AMQPBaseActor
from sdsstools import merge_config, read_yaml_file

from lvmieb import config
from lvmieb.actor.actor import lvmieb as IebActor
from lvmieb.controller.controller import IebController


# Exposure shutter commands

expCmds = {
    "QX1": "init",
    "QX2": "home",
    "QX3": "open",
    "QX4": "close",
    "QX5": "flash",
    "QX8": "on",
    "QX9": "off",
    "QX10": "ssroff",
    "QX11": "ssron",
    "IS": "status",
}

# Hartmann Door commands

hdCmds = {"QX1": "init", "QX2": "home", "QX3": "open", "QX4": "close", "IS": "status"}

hr_status = "closed"
hl_status = "closed"
sh_status = "closed"


@pytest.fixture()
def test_config():

    extra = read_yaml_file(os.path.join(os.path.dirname(__file__), "test_actor.yml"))
    yield merge_config(extra, config)


@pytest.fixture
async def hartmann_right(request, unused_tcp_port_factory: int):
    """Mocks a hartmann door right that replies to commands with predefined replies."""

    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        global hr_status
        while True:
            data = await reader.readuntil(b"\r")
            matched = re.search(b"(QX1|QX2|QX3|QX4|IS)", data)
            print(matched)
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                cmd = hdCmds[cmd]
                print(f"command is now {cmd}!")

                if cmd == "open":
                    await asyncio.sleep(1.7)
                    hr_status = "opened"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hr_status == "opened"
                elif cmd == "close":
                    await asyncio.sleep(1.7)
                    hr_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hr_status == "closed"
                elif cmd == "init":
                    # await asyncio.sleep(1)
                    hr_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hr_status == "closed"
                elif cmd == "home":
                    # await asyncio.sleep(1)
                    hr_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hr_status == "closed"
                elif cmd == "status":
                    if hr_status == "opened":
                        writer.write(b"\x00\x07IS=10111111\r")
                    elif hr_status == "closed":
                        writer.write(b"\x00\x07IS=01111111\r")
                await writer.drain()
                print(hr_status)

    port_hart_right = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_hart_right)
    async with server:
        hr = IebController(
            host="localhost", port=port_hart_right, name="hartmann_right", spec="sp1"
        )
        yield hr
    server.close()


@pytest.fixture
async def hartmann_left(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        global hl_status
        while True:
            data = await reader.readuntil(b"\r")
            matched = re.search(b"(QX1|QX2|QX3|QX4|IS)", data)
            print(matched)
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                cmd = hdCmds[cmd]
                print(f"command is now {cmd}!")
                if cmd == "open":
                    await asyncio.sleep(1.7)
                    hl_status = "opened"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hl_status == "opened"
                elif cmd == "close":
                    await asyncio.sleep(1.7)
                    hl_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hl_status == "closed"
                elif cmd == "init":
                    # await asyncio.sleep(1)
                    hl_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hl_status == "closed"
                elif cmd == "home":
                    # await asyncio.sleep(1)
                    hl_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert hl_status == "closed"
                elif cmd == "status":
                    if hl_status == "opened":
                        writer.write(b"\x00\x07IS=01111111\r")
                    elif hl_status == "closed":
                        writer.write(b"\x00\x07IS=10111111\r")
                await writer.drain()

    port_hart_left = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_hart_left)
    async with server:
        hl = IebController(
            "localhost", port_hart_left, name="hartmann_left", spec="sp1"
        )
        yield hl
    server.close()


@pytest.fixture
async def shutter(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        global sh_status
        print(sh_status)
        while True:
            data = await reader.readuntil(b"\r")
            matched = re.search(b"(QX1|QX2|QX3|QX4|IS)", data)
            print(matched)
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                cmd = expCmds[cmd]
                print(f"command is now {cmd}!")

                if cmd == "open":
                    await asyncio.sleep(0.61)
                    sh_status = "opened"
                    writer.write(b"\x00\x07%DONE\r")
                    assert sh_status == "opened"
                elif cmd == "close":
                    await asyncio.sleep(0.61)
                    sh_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert sh_status == "closed"
                elif cmd == "init":
                    await asyncio.sleep(1)
                    sh_status = "closed"
                    writer.write(b"\x00\x07%DONE\r")
                    assert sh_status == "closed"
                elif cmd == "status":
                    if sh_status == "opened":
                        writer.write(b"\x00\x07IS=10111111\r")
                    elif sh_status == "closed":
                        writer.write(b"\x00\x07IS=01111111\r")
                await writer.drain()
                print(sh_status)

    port_shutter = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_shutter)
    async with server:
        sh = IebController("localhost", port_shutter, name="shutter", spec="sp1")
        yield sh
    server.close()


@pytest.fixture
async def depth(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            data = await reader.readuntil(b"\n")
            print(data)
            matched = re.search(b"(A|B|C)", data)
            print(matched)
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                print(f"command is now {cmd}!")

                if cmd == "A":
                    writer.write(b"A -60.195 mm \n")
                elif cmd == "B":
                    writer.write(b"\rB -60.875 mm \n")
                elif cmd == "C":
                    writer.write(b"\rC -60.711 mm \n")
                await writer.drain()

    port_depth = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_depth)
    async with server:
        sh = IebController("localhost", port_depth, name="sp1", spec="sp1")
        yield sh
    server.close()


@pytest.fixture
async def transducer_r1(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            data = await reader.readuntil(b"?\\")
            print(data)
            matched = re.search(b"(P|T)", data)
            print(matched)
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                print(f"command is now {cmd}!")

                if cmd == "P":
                    writer.write(b"@253ACK1.7380E-04\\")
                elif cmd == "T":
                    writer.write(b"@253ACK23.15\\")
                await writer.drain()

    port_trans = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_trans)
    async with server:
        sh = IebController("localhost", port_trans, name="r1", spec="sp1")
        yield sh
    server.close()


@pytest.fixture
async def transducer_b1(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            data = await reader.readuntil(b"?\\")
            print(data)
            matched = re.search(b"(P|T)", data)
            print(matched)
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                print(f"command is now {cmd}!")

                if cmd == "P":
                    writer.write(b"@253ACK2.4180E-04\\")
                elif cmd == "T":
                    writer.write(b"@253ACK23.09\\")
                await writer.drain()

    port_trans_b1 = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_trans_b1)
    async with server:
        sh = IebController("localhost", port_trans_b1, name="b1", spec="sp1")
        yield sh
    server.close()


@pytest.fixture
async def transducer_z1(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            data = await reader.readuntil(b"?\\")
            print(data)
            matched = re.search(b"(P|T)", data)
            print(matched)
            if not matched:
                continue
            else:
                com = matched.group()
                cmd = com.decode()
                print(f"command is now {cmd}!")

                if cmd == "P":
                    writer.write(b"@253ACK1.7420E-04\\")
                elif cmd == "T":
                    writer.write(b"@253ACK22.03\\")
                await writer.drain()

    port_trans = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_trans)
    async with server:
        sh = IebController("localhost", port_trans, name="z1", spec="sp1")
        yield sh
    server.close()


@pytest.fixture
async def labsensor(request, unused_tcp_port_factory: int):
    async def handle_connection(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        while True:
            data = await reader.readuntil(b"\n")
            print(data)
            writer.write(b"E0:13:D5:71:D0:66 23.0 42.6 0 2022-04-10T07:32:16.078590\n")
            await writer.drain()

    port_lab = unused_tcp_port_factory()
    server = await asyncio.start_server(handle_connection, "localhost", port_lab)
    async with server:
        sh = IebController("localhost", port_lab, name="sensor", spec="sp1")
        yield sh
    server.close()


@pytest.fixture
def controllers(
    shutter: IebController,
    hartmann_left: IebController,
    hartmann_right: IebController,
    depth: IebController,
    transducer_r1: IebController,
    transducer_b1: IebController,
    transducer_z1: IebController,
    labsensor: IebController,
):
    controllers = {}
    controllers.update({shutter.name: shutter})
    controllers.update({hartmann_right.name: hartmann_right})
    controllers.update({hartmann_left.name: hartmann_left})
    controllers.update({depth.name: depth})
    controllers.update({transducer_r1.name: transducer_r1})
    controllers.update({transducer_b1.name: transducer_b1})
    controllers.update({transducer_z1.name: transducer_z1})
    controllers.update({labsensor.name: labsensor})

    print(f"spec is {shutter.spec}")

    # print(hartmann_left)
    # print(hartmann_right)

    return controllers


@pytest.fixture()
async def actor(controllers, test_config: dict, mocker):

    # We need to call the actor .start() method to force it to create the
    # controllers and to start the tasks, but we don't want to run .start()
    # on the actor.

    mocker.patch.object(AMQPBaseActor, "start")

    _actor = IebActor.from_config(test_config)

    _actor.parser_args = [controllers]
    await _actor.start()

    _actor = await clu.testing.setup_test_actor(_actor)  # type: ignore

    yield _actor

    _actor.mock_replies.clear()
    await _actor.stop()
