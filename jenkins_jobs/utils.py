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

import fnmatch
from pprint import pformat
import re

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.formatter import CustomFormatter


def deep_format(obj, paramdict, allow_empty=False):
    """Apply the paramdict via str.format() to all string objects found within
       the supplied obj. Lists and dicts are traversed recursively."""
    # YAML serialisation was originally used to achieve this, but that places
    # limitations on the values in paramdict - the post-format result must
    # still be valid YAML (so substituting-in a string containing quotes, for
    # example, is problematic).
    if hasattr(obj, 'format'):
        try:
            result = re.match('^{obj:(?P<key>\w+)}$', obj)
            if result is not None:
                ret = paramdict[result.group("key")]
            else:
                ret = CustomFormatter(allow_empty).format(obj, **paramdict)
        except KeyError as exc:
            missing_key = exc.message
            desc = "%s parameter missing to format %s\nGiven:\n%s" % (
                missing_key, obj, pformat(paramdict))
            raise JenkinsJobsException(desc)
    elif isinstance(obj, list):
        ret = []
        for item in obj:
            ret.append(deep_format(item, paramdict, allow_empty))
    elif isinstance(obj, dict):
        ret = {}
        for item in obj:
            try:
                ret[CustomFormatter(allow_empty).format(item, **paramdict)] = \
                    deep_format(obj[item], paramdict, allow_empty)
            except KeyError as exc:
                missing_key = exc.message
                desc = "%s parameter missing to format %s\nGiven:\n%s" % (
                    missing_key, obj, pformat(paramdict))
                raise JenkinsJobsException(desc)
    else:
        ret = obj
    return ret


def matches(what, glob_patterns):
    """
    Checks if the given string, ``what``, matches any of the glob patterns in
    the iterable, ``glob_patterns``

    :arg str what: String that we want to test if it matches a pattern
    :arg iterable glob_patterns: glob patterns to match (list, tuple, set,
    etc.)
    """
    return any(fnmatch.fnmatch(what, glob_pattern)
               for glob_pattern in glob_patterns)
