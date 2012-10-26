#!/usr/bin/env python
#
# Joint copyright:
#  - Copyright 2012 Wikimedia Foundation
#  - Copyright 2012 Antoine "hashar" Musso
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
import re
import testtools
#import jenkins_jobs.modules.publishers
from jenkins_jobs.modules import publishers

FIXTURES_PATH = os.path.join(os.path.dirname(__file__),
        'fixtures')


class testModuleXunit(testtools.TestCase):

    def test_xunit_snippets(case):
        fixtures = os.listdir(FIXTURES_PATH)

        yaml_files = [f for f in fixtures if re.match(r'.*yaml', f)]

        print "\nAnalyzing %s\n" % yaml_files
        for yaml_file in yaml_files:
            xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_file)
            print "Testing %s" % xml_candidate
            if xml_candidate not in fixtures:
                print xml_candidate
                raise Exception("No XML file named '%s' to match " +
                    "YAML file '%s'" % (xml_candidate, yaml_file))

        print yaml_files

    def check_xunit_output(expected_xml, yaml_input):
        #publishers.xunit(1,2,3)
        assert 'foo' == 'bar'
