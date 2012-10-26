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

import difflib
import os
import re
import sys
import testtools
from testtools.content import text_content
from testtools.matchers import Equals
import yaml

import xml.etree.ElementTree as XML
from jenkins_jobs.builder import XmlJob, YamlParser
from jenkins_jobs.modules import publishers

FIXTURES_PATH = os.path.join(os.path.dirname(__file__),
        'fixtures')


class TestModulePublishers(testtools.TestCase):

    # Pretty printing ideas from
    # http://stackoverflow.com/questions/749796/pretty-printing-xml-in-python
    pretty_text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)

    def get_fixtures(self):
        """Returns a list of dicts:
            'yaml' : content of the fixture .yaml file
            'xml'  : content of the fixture .xml file
        """
        fixtures = []
        files = os.listdir(FIXTURES_PATH)
        yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

        for yaml_file in yaml_files:
            xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_file)
            # Make sure the yaml file has a xml counterpart
            if xml_candidate not in files:
                raise Exception("No XML file named '%s' to match " +
                    "YAML file '%s'" % (xml_candidate, yaml_file))

            # Read XML content, assuming it is unicode encoded
            xml_filename = os.path.join(FIXTURES_PATH, xml_candidate)
            xml_content = u"%s" % open(xml_filename, 'r').read()

            yaml_file = file(os.path.join(FIXTURES_PATH, yaml_file), 'r')
            yaml_content = yaml.load(yaml_file)

            fixtures.append({'yaml': yaml_content, 'xml': xml_content})

        return fixtures

    def test_yaml_snippets(self):
        for fixture in self.get_fixtures():
            print fixture['yaml']
            print yaml.dump(fixture['yaml'])

            xml_project = XML.Element('project')  # root element
            parser = YamlParser()
            pub = publishers.Publishers(ModuleRegistry())

            # Generate the XML tree directly with modules/publishers/*
            pub.gen_xml(parser, xml_project, fixture['yaml'])

            # Prettify generated XML
            pretty_xml = XmlJob(xml_project, 'fixturejob').output()

            # Unified diff:
            udiff = list(difflib.unified_diff(
                fixture['xml'].splitlines(1),
                pretty_xml.splitlines(1),
                fromfile="expected.xml",
                tofile="actual.xml"
                ))

            if len(udiff) == 0:
                self.assertEquals('actual', 'actual',  # HACK
                    "Generated XML should match expected fixture.")
            else:
                self.addDetail('xml-diff', text_content(''.join(udiff)))
                self.assertEquals('actual', 'expected',
                    "Generated XML does not match expected fixture.")


class ModuleRegistry(object):
    """ Mock of jenkins_jobs.ModuleRegistry class """
