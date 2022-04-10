import pytest

from lvmieb.actor.actor import lvmieb as IebActor


@pytest.mark.asyncio
async def test_depth_status(actor: IebActor):

    # initial state with the linear gauges are not initialized
    print(actor.parser_args[0])
    assert actor.parser_args[0]["sp1"].depth == {"A": -999.0, "B": -999.0, "C": -999.0}

    command = await actor.invoke_mock_command("depth status")
    await command
    assert command.status.did_succeed

    assert actor.parser_args[0]["sp1"].depth == {
        "A": -60.195,
        "B": -60.875,
        "C": -60.711,
    }
    assert command.replies[-2].message["sp1"]["z1"]["A"] == -60.195
    assert command.replies[-2].message["sp1"]["z1"]["B"] == -60.875
    assert command.replies[-2].message["sp1"]["z1"]["C"] == -60.711
