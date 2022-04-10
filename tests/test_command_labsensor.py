import pytest

from lvmieb.actor.actor import lvmieb as IebActor


@pytest.mark.asyncio
async def test_labsensor(actor: IebActor):

    # initial state with the linear gauges are not initialized
    print(actor.parser_args[0])
    assert actor.parser_args[0]["sensor"].labtemp == -999
    assert actor.parser_args[0]["sensor"].labhum == -1

    command = await actor.invoke_mock_command("labtemp")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["sensor"].labtemp == 23.0
    assert actor.parser_args[0]["sensor"].labhum == 42.6

    assert command.replies[-2].message["labtemp"] == 23.0
    assert command.replies[-2].message["labhum"] == 42.6
