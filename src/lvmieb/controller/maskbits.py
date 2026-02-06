#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import enum


__all__ = ["MotorStatus"]


class MotorStatus(enum.Flag):
    """Status bits for motor status."""

    POWER_ON = 0x1
    POWER_OFF = 0x2
    POWER_UNKNOWN = 0x4
    OPEN = 0x10
    CLOSED = 0x20
    POSITION_INVALID = 0x40
    POSITION_UNKNOWN = 0x80
