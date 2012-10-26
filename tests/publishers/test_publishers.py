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
import yaml

import xml.etree.ElementTree as XML
from jenkins_jobs.builder import YamlParser

#import jenkins_jobs.modules.publishers
from jenkins_jobs.modules import publishers

FIXTURES_PATH = os.path.join(os.path.dirname(__file__),
        'fixtures')


class TestModulePublishers(testtools.TestCase):

    def test_equality(self):
        self.assertEqual('foo', 'foo')

    def get_fixtures(self):
        fixtures = []
        files = os.listdir(FIXTURES_PATH)
        yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

        for yaml_file in yaml_files:
            xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_file)
            # Make sure the yaml file has a xml counterpart
            if xml_candidate not in files:
                raise Exception("No XML file named '%s' to match " +
                    "YAML file '%s'" % (xml_candidate, yaml_file))

            xml_filename = os.path.join(FIXTURES_PATH, xml_candidate)
            xml_content = open(xml_filename, 'r').read()

            yaml_file = file(os.path.join(FIXTURES_PATH, yaml_file), 'r')
            yaml_content = yaml.load(yaml_file)

            fixtures.append({'yaml': yaml_content, 'xml': xml_content})

        return fixtures

    def test_yaml_snippets(self):
        for fixture in self.get_fixtures():
            print fixture['yaml']
            print yaml.dump(fixture['yaml'])

            xml_project = XML.Element('project')
            parser = YamlParser()
            pub = publishers.Publishers(ModuleRegistry())

            # Generate the XML tree directly with modules/publishers/*
            pub.gen_xml(parser, xml_project, fixture['yaml'])

            # Fixme: pretty print generated XML
            self.assertEquals(fixture['xml'], XML.tostring(xml_project))


class ModuleRegistry(object):
    """ Mock of jenkins_jobs.ModuleRegistry class """
