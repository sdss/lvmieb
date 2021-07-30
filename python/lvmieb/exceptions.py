# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Changgon Kim, Mingeyong Yang, Taeeun Kim
# @Date:    2021-04-26 17:14
# @Last modified by:   Changgon Kim

from __future__ import print_function, division, absolute_import


class LvmIebError(Exception):
    """A custom core LvmIeb exception"""

    def __init__(self, message=None):

        message = 'There has been an error' \
            if not message else message

        super(LvmIebError, self).__init__(message)


class LvmIebNotImplemented(LvmIebError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = 'This feature is not implemented yet.' \
            if not message else message

        super(LvmIebNotImplemented, self).__init__(message)


class LvmIebAPIError(LvmIebError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = 'Error with Http Response from LvmIeb API'
        else:
            message = 'Http response error from LvmIeb API. {0}'.format(message)

        super(LvmIebAPIError, self).__init__(message)


class LvmIebApiAuthError(LvmIebAPIError):
    """A custom exception for API authentication errors"""
    pass


class LvmIebMissingDependency(LvmIebError):
    """A custom exception for missing dependencies."""
    pass


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
