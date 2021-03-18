# !usr/bin/env python
# -*- coding: utf-8 -*-
#
# Licensed under a 3-clause BSD license.
#
# @Author: Brian Cherinka
# @Date:   2017-12-05 12:01:21
# @Last modified by:   Brian Cherinka
# @Last Modified time: 2017-12-05 12:19:32

from __future__ import print_function, division, absolute_import


class OsuActorError(Exception):
    """A custom core OsuActor exception"""

    def __init__(self, message=None):

        message = 'There has been an error' \
            if not message else message

        super(OsuActorError, self).__init__(message)


class OsuActorNotImplemented(OsuActorError):
    """A custom exception for not yet implemented features."""

    def __init__(self, message=None):

        message = 'This feature is not implemented yet.' \
            if not message else message

        super(OsuActorNotImplemented, self).__init__(message)


class OsuActorAPIError(OsuActorError):
    """A custom exception for API errors"""

    def __init__(self, message=None):
        if not message:
            message = 'Error with Http Response from OsuActor API'
        else:
            message = 'Http response error from OsuActor API. {0}'.format(message)

        super(OsuActorAPIError, self).__init__(message)


class OsuActorApiAuthError(OsuActorAPIError):
    """A custom exception for API authentication errors"""
    pass


class OsuActorMissingDependency(OsuActorError):
    """A custom exception for missing dependencies."""
    pass


class OsuActorWarning(Warning):
    """Base warning for OsuActor."""


class OsuActorUserWarning(UserWarning, OsuActorWarning):
    """The primary warning class."""
    pass


class OsuActorSkippedTestWarning(OsuActorUserWarning):
    """A warning for when a test is skipped."""
    pass


class OsuActorDeprecationWarning(OsuActorUserWarning):
    """A warning for deprecated features."""
    pass
