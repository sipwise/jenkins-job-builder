#
# Copyright (c) 2016 Kien Ha <kienha9922@gmail.com>
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

import testtools
from testtools.matchers import Equals
import xml.etree.ElementTree as XML
import yaml

from jenkins_jobs.errors import MissingAttributeError
from jenkins_jobs.modules.helpers import convert_mapping_to_xml_fail_required
from tests.base import LoggingFixture


class TestCaseTestHelpers(LoggingFixture, testtools.TestCase):

    def test_convert_mapping_to_xml_fail_required(self):
        """
        Tests the test_convert_mapping_to_xml_fail_required function
        """

        # Test default values
        default_data = yaml.load("string: hello")
        default_mappings = [('default-string', 'defaultString', 'default')]
        default_root = XML.Element('testdefault')
        convert_mapping_to_xml_fail_required(default_data, default_root,
                                             default_mappings)
        result = default_root.find('defaultString').text
        self.assertThat(result, Equals('default'))

        # Test user input
        user_input_data = yaml.load("user-input-string: hello")
        user_input_mappings = [('user-input-string', 'userInputString',
                                'user-input')]
        user_input_root = XML.Element('testUserInput')
        convert_mapping_to_xml_fail_required(user_input_data, user_input_root,
                                             user_input_mappings)
        result = user_input_root.find('userInputString').text
        self.assertThat(result, Equals('hello'))

        # Test missing required input
        required_data = yaml.load("string: hello")
        required_mappings = [('required-string', 'requiredString', None)]
        required_root = XML.Element('testrequired')
        self.assertRaises(MissingAttributeError,
                          convert_mapping_to_xml_fail_required,
                          required_data, required_root, required_mappings)
