# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Changgon Kim, Mingeyong Yang, Taeeun Kim
# @Date:    2021-04-26 17:14
# @Last modified by:   Changgon Kim

from __future__ import annotations


class LvmIebError(Exception):
    """A custom core LvmIeb exception"""

    def __init__(self, message=None):

        message = "There has been an error" if not message else message

        super(LvmIebError, self).__init__(message)


class MotorControllerError(LvmIebError):
    """A motor controller error."""


class LvmIebWarning(Warning):
    """Base warning for LvmIeb."""


class LvmIebUserWarning(UserWarning, LvmIebWarning):
    """The primary warning class."""

    pass


class LvmIebSkippedTestWarning(LvmIebUserWarning):
    """A warning for when a test is skipped."""

    pass


class LvmIebDeprecationWarning(LvmIebUserWarning):
    """A warning for deprecated features."""

    pass
