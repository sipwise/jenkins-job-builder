#!/usr/bin/env python
# Copyright (C) 2015 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Manage JJB yaml feature implementation

import logging
from string import Formatter

logger = logging.getLogger(__name__)


class CustomFormatter(Formatter):
    """
    Custom formatter to allow non-existing key references when formatting a
    string
    """
    def __init__(self, allow_empty=False):
        super(CustomFormatter, self).__init__()
        self.allow_empty = allow_empty

    def get_value(self, key, args, kwargs):
        try:
            return Formatter.get_value(self, key, args, kwargs)
        except KeyError:
            if self.allow_empty:
                logger.debug(
                    'Found uninitialized key %s, replaced with empty string',
                    key
                )
                return ''
            raise
