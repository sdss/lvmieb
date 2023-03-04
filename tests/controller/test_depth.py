#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-12
# @Filename: test_depth.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import pytest

from lvmieb.controller.depth import DepthGauges

from ..mockers import DepthMocker


async def get_depth_controller(use_r=False, custom_reply=None):
    mock_depth = DepthMocker()
    mock_depth.use_r = use_r
    mock_depth.custom_reply = custom_reply

    await mock_depth.start()

    return DepthGauges("localhost", mock_depth.port)


@pytest.mark.parametrize("use_r", [True, False])
async def test_read(use_r: bool):
    depth_controller = await get_depth_controller(use_r=use_r)
    depth = await depth_controller.read()

    assert depth == {"A": 1.5, "B": 1.5, "C": 1.5}


async def test_read_fails():
    depth_controller = DepthGauges("localhost", 123456)

    with pytest.raises(ValueError):
        await depth_controller.read()


@pytest.mark.parametrize("use_r", [True, False])
async def test_read_bad_reply(use_r: bool):
    prefix = b"\r" if use_r else b""
    depth_controller = await get_depth_controller(
        use_r=use_r,
        custom_reply=prefix + b"XXX\n",
    )

    with pytest.raises(ValueError):
        print(await depth_controller.read())
