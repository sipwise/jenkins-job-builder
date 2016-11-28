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

from tests.cmd.test_cmd import CmdTestsBase
import mock
import os


@mock.patch('uuid.uuid4', mock.Mock(return_value='1-1-1-1-1'))
class TestCaseMultibranchPipeline(CmdTestsBase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    default_config_file = '/dev/null'

    def test_multibranch(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """
        self._assert_yaml2xml('project_multibranch_template001.yaml',
                              'project_multibranch_template001.xml')

    def test_multibranch_defaults(self):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """
        self._assert_yaml2xml('project_multibranch_template002.yaml',
                              'project_multibranch_template002.xml')
