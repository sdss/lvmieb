import pytest

from lvmieb.actor.actor import lvmieb as IebActor


@pytest.mark.asyncio
async def test_shutter_status(actor: IebActor):
    # initial state with the shutter not initialized
    assert actor.parser_args[0]["shutter"].shutter_status is None

    # initialize the shutter with shutter init command
    command = await actor.invoke_mock_command("shutter init")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["shutter"].shutter_status == "closed"

    # run the shutter status command to the actor
    command = await actor.invoke_mock_command("shutter status")
    await command
    assert command.status.did_succeed

    # check if the virtual shutter is closed
    assert actor.parser_args[0]["shutter"].shutter_status == "closed"
    assert command.replies[-2].message["sp1"]["shutter"] == "closed"


@pytest.mark.asyncio
async def test_shutter_open_and_close(actor: IebActor):

    # initial state with the shutter not initialized
    assert actor.parser_args[0]["shutter"].shutter_status is None

    # initialize the shutter with shutter init command
    command = await actor.invoke_mock_command("shutter init")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["shutter"].shutter_status == "closed"

    # check the status of the shutter
    command = await actor.invoke_mock_command("shutter status")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["shutter"].shutter_status == "closed"
    assert command.replies[-2].message["sp1"]["shutter"] == "closed"

    # open the closed shutter
    command = await actor.invoke_mock_command("shutter open")
    await command
    assert command.status.did_succeed

    # check the status of the virtual shutter is opened
    assert actor.parser_args[0]["shutter"].shutter_status == "opened"
    assert command.replies[-2].message["sp1"]["shutter"] == "opened"

    # check again if the status od the virtual shutter is same
    command = await actor.invoke_mock_command("shutter status")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["shutter"].shutter_status == "opened"
    assert command.replies[-2].message["sp1"]["shutter"] == "opened"

    # close the opened shutter
    command = await actor.invoke_mock_command("shutter close")
    await command
    assert command.status.did_succeed

    # check the status of the virtual shutter is closed
    assert actor.parser_args[0]["shutter"].shutter_status == "closed"
    assert command.replies[-2].message["sp1"]["shutter"] == "closed"
