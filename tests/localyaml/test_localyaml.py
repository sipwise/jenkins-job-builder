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
from jenkins_jobs import local_yaml as yaml


class TestCaseLocalYamlInclude(TestWithScenarios, TestCase, BaseTestCase):
    """
    Verify application specific tags independently of any changes to
    modules XML parsing behaviour
    """
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    scenarios = get_scenarios(fixtures_path, 'yaml', 'json')

    def __read_content(self):
        # Read yaml content, assuming it is unicode encoded
        json_filepath = os.path.join(self.fixtures_path, self.json_filename)
        json_content = u"%s" % open(json_filepath, 'r').read()

        yaml_filepath = os.path.join(self.fixtures_path, self.yaml_filename)
        with file(yaml_filepath, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)

        return (yaml_content, json_content)

    def test_yaml_snippet(self):
        if not self.json_filename or not self.yaml_filename:
            return

        data, expected_json = self.__read_content()

        pretty_json = json.dumps(data, indent=4, separators=(',', ': '))

        self.assertThat(
            pretty_json,
            testtools.matchers.DocTestMatches(expected_json,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )
