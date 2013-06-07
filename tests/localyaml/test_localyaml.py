#!/usr/bin/env python
#
# Copyright 2013 Darragh Bailey
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

import os
import doctest
import testtools
import json
from testtools import TestCase
from testscenarios.testcase import TestWithScenarios
from tests.base import get_scenarios, BaseTestCase


class TestCaseLocalYamlInclude(TestWithScenarios, TestCase, BaseTestCase):
    """
    Verify application specific tags independently of any changes to
    modules XML parsing behaviour
    """
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = get_scenarios(fixtures_path, 'yaml', 'json')

    __read_content = getattr(BaseTestCase, '_BaseTestCase__read_content')

    def test_yaml_snippet(self):
        if not self.out_filename or not self.in_filename:
            return

        yaml_content, expected_json = self.__read_content()

        pretty_json = json.dumps(yaml_content, indent=4,
                                 separators=(',', ': '))

        self.assertThat(
            pretty_json,
            testtools.matchers.DocTestMatches(expected_json,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )
