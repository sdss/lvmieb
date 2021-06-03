#!/usr/bin/env python                                                                                                                                          
# -*- coding: utf-8 -*-
#
# @Author: Mingyeong YANG (mingyeong@khu.ac.kr)
# @Date: 2021-05-25
# @Filename: test_controller.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import pytest

from lvmieb.controller.controller import IebController
from lvmieb.exceptions import (
    LvmIebError,
    LvmIebNotImplemented,
    LvmIebAPIError,
    LvmIebApiAuthError,
    LvmIebMissingDependency,
    LvmIebWarning,
    LvmIebUserWarning,
    LvmIebSkippedTestWarning,
    LvmIebDeprecationWarning,
)

@pytest.mark.asyncio
async def test_hartmann_door_connection(hartmann_right: IebController):
    assert hartmann_right.host == "localhost"
    assert hartmann_right.name == "hartmann_right"
    await hartmann_right.connect()
    assert hartmann_right.connected == True
    #await hartmann_right.connect()

    await hartmann_right.disconnect()
    assert hartmann_right.connected == False

