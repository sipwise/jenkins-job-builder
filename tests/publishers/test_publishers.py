#!/usr/bin/env python
#
# Joint copyright:
#  - Copyright 2012,2013 Wikimedia Foundation
#  - Copyright 2012,2013 Antoine "hashar" Musso
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
import unittest
import xml.etree.ElementTree as XML
import yaml

from jenkins_jobs.builder import XmlJob, YamlParser, ModuleRegistry
from jenkins_jobs.modules import publishers

FIXTURES_PATH = os.path.join(
    os.path.dirname(__file__), 'fixtures')


def get_fixtures():
    """Returns a list of tuples containing, in order:
        - content of the fixture .yaml file
        - content of the fixture .xml file
        - list of the filenames
    """
    fixtures = []
    files = os.listdir(FIXTURES_PATH)
    yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

    for yaml_filename in yaml_files:
        xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_filename)
        # Make sure the yaml file has a xml counterpart
        if xml_candidate not in files:
            raise Exception(
                "No XML file named '%s' to match " +
                "YAML file '%s'" % (xml_candidate, yaml_filename))

        # Read XML content, assuming it is unicode encoded
        xml_filename = os.path.join(FIXTURES_PATH, xml_candidate)
        xml_content = u"%s" % open(xml_filename, 'r').read()

        yaml_file = file(os.path.join(FIXTURES_PATH, yaml_filename), 'r')
        yaml_content = yaml.load(yaml_file)

        fixtures.append((
            yaml_content,
            xml_content,
            [xml_filename, yaml_filename],
        ))

    return fixtures


def build_testcases(name, bases, d):
    def build_test_method(yamldef, xml, files):
        def test(self):
            self.core_yaml_snippet(yamldef, xml, files)
        return test

    for yamldef, xml, files in get_fixtures():
        # Transform the file name so that it can be used as a method name.
        normalized_name = os.path.basename(files[1]).replace('.', '_')
        d['test_%s' % normalized_name] = build_test_method(yamldef, xml, files)

    return type(name, bases, d)


class TestCaseModulePublisher(testtools.TestCase):
    __metaclass__ = build_testcases

    # testtools.TestCase settings:
    maxDiff = None      # always dump text difference
    longMessage = True  # keep normal error message when providing our

    def core_yaml_snippet(self, yaml, expected_xml, files):
        xml_project = XML.Element('project')  # root element
        parser = YamlParser()
        pub = publishers.Publishers(ModuleRegistry({}))

        # Generate the XML tree directly with modules/publishers/*
        pub.gen_xml(parser, xml_project, yaml)

        # Prettify generated XML
        pretty_xml = XmlJob(xml_project, 'fixturejob').output()

        self.assertMultiLineEqual(
            expected_xml, pretty_xml,
            'Test inputs: %s' % ', '.join(files)
        )

if __name__ == "__main__":
    unittest.main()
