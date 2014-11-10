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

import mock
from six.moves import configparser
from six.moves import StringIO
import testtools

from jenkins_jobs import cmd


class CmdTestsBase(testtools.TestCase):

    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    parser = cmd.create_parser()

    def setUp(self):
        super(CmdTestsBase, self).setUp()

        # Testing the cmd module can sometimes result in the CacheStorage class
        # attempting to create the cache directory multiple times as the tests
        # are run in parallel.  Stub out the CacheStorage to ensure that each
        # test can safely create the cache directory without risk of
        # interference.
        self.cache_patch = mock.patch('jenkins_jobs.builder.CacheStorage',
                                      autospec=True)
        self.cache_patch.start()

        self.config = configparser.ConfigParser()
        self.config.readfp(StringIO(cmd.DEFAULT_CONF))

    def tearDown(self):
        self.cache_patch.stop()
        super(CmdTestsBase, self).tearDown()


class CmdTests(CmdTestsBase):

    def test_with_empty_args(self):
        """
        User passes no args, should fail with SystemExit
        """
        with mock.patch('sys.stderr'):
            self.assertRaises(SystemExit, cmd.main, [])
