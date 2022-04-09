import pytest

from lvmieb.actor.actor import lvmieb as IebActor


@pytest.mark.asyncio
async def test_hartmann_init_and_home(actor: IebActor):

    # initial state with the hartmann doors not initialized
    print(actor.parser_args[0])
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status is None
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status is None

    # initialize the shutter with hartmann init command
    command = await actor.invoke_mock_command("hartmann init")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "closed"
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "closed"

    # homing the shutter with hartmann home command
    command = await actor.invoke_mock_command("hartmann home")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "closed"
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "closed"

    # run the hartmann status command to the actor
    command = await actor.invoke_mock_command("hartmann status")
    await command
    assert command.status.did_succeed

    # check if the virtual hartmann doors are closed
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "closed"
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_left"] == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_right"] == "closed"


@pytest.mark.asyncio
async def test_shutter_open_and_close(actor: IebActor):

    # initial state with the hartmann doors not initialized
    print(actor.parser_args[0])
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status is None
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status is None

    # initialize the shutter with hartmann init command
    command = await actor.invoke_mock_command("hartmann init")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "closed"
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "closed"

    # run the hartmann status command to the actor
    command = await actor.invoke_mock_command("hartmann status")
    await command
    assert command.status.did_succeed

    # check if the virtual hartmann doors are closed
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "closed"
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_left"] == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_right"] == "closed"

    # open the both hartmann doors
    command = await actor.invoke_mock_command("hartmann open --side=all")
    await command
    assert command.status.did_succeed

    # check the status of the virtual hartmann doors are opened
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "opened"
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "opened"
    assert command.replies[-2].message["sp1"]["hartmann_left"] == "opened"
    assert command.replies[-2].message["sp1"]["hartmann_right"] == "opened"

    # check again if the status of the virtual doors are same
    command = await actor.invoke_mock_command("hartmann status")
    await command
    assert command.status.did_succeed
    assert command.replies[-2].message["sp1"]["hartmann_left"] == "opened"
    assert command.replies[-2].message["sp1"]["hartmann_right"] == "opened"

    # close both of the hartmann doors
    command = await actor.invoke_mock_command("hartmann close --side=all")
    await command
    assert command.status.did_succeed

    # check the status of the virtual hartmann doors are closed
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "closed"
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_left"] == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_right"] == "closed"

    # open left hartmann door
    command = await actor.invoke_mock_command("hartmann open --side=left")
    await command
    assert command.status.did_succeed

    # check the left status
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "opened"
    assert command.replies[-2].message["sp1"]["hartmann_left"] == "opened"

    # open right hartmann door
    command = await actor.invoke_mock_command("hartmann open --side=right")
    await command
    assert command.status.did_succeed

    # check the right status
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "opened"
    assert command.replies[-2].message["sp1"]["hartmann_right"] == "opened"

    # close left hartmann door
    command = await actor.invoke_mock_command("hartmann close --side=left")
    await command
    assert command.status.did_succeed

    # check the left status
    assert actor.parser_args[0]["hartmann_left"].hartmann_left_status == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_left"] == "closed"

    # close right hartmann door
    command = await actor.invoke_mock_command("hartmann close --side=right")
    await command
    assert command.status.did_succeed

    # check the right status
    assert actor.parser_args[0]["hartmann_right"].hartmann_right_status == "closed"
    assert command.replies[-2].message["sp1"]["hartmann_right"] == "closed"
