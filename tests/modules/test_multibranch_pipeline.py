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
import io
import mock
import os
import uuid


class TestCaseMultibranchPipeline(CmdTestsBase):

    @mock.patch.object(uuid, 'uuid4', return_value='1-1-1-1-1')
    def test_pipeline_multibranch(self, mock_class):
        """
        Run test mode and verify that resulting XML gets sent to the console.
        """

        self.fixtures_path = os.path.join(os.path.dirname(__file__),
                                          'fixtures')
        self.default_config_file = '/dev/null'

        console_out = io.BytesIO()
        with mock.patch('sys.stdout', console_out):
            args = ['--conf', self.default_config_file, 'test',
                    os.path.join(self.fixtures_path, 'project_pipeline_multibranch_template001.yaml')]  # noqa

            self.execute_jenkins_jobs_with_args(args)
        xml_content = io.open(os.path.join(self.fixtures_path, 'project_pipeline_multibranch_template001.xml'),  # noqa
                              'r', encoding='utf-8').read()
        self.assertEqual(console_out.getvalue().decode('utf-8'), xml_content)
