from __future__ import absolute_import
import doctest
import os
from testscenarios.testcase import TestWithScenarios
import testtools
import xml.etree.ElementTree as XML
import yaml

from jenkins_jobs.builder import XmlJob, YamlParser, ModuleRegistry
from jenkins_jobs.modules import general

from ..base import get_scenarios


FIXTURES_PATH = os.path.join(
    os.path.dirname(__file__), 'fixtures')


class TestCaseModuleGeneral(TestWithScenarios, testtools.TestCase):
    scenarios = get_scenarios(FIXTURES_PATH)

    # TestCase settings:
    maxDiff = None      # always dump text difference
    longMessage = True  # keep normal error message when providing our

    def __read_content(self):
        # Read XML content, assuming it is unicode encoded
        xml_filepath = os.path.join(FIXTURES_PATH, self.xml_filename)
        xml_content = u"%s" % open(xml_filepath, 'r').read()

        yaml_filepath = os.path.join(FIXTURES_PATH, self.yaml_filename)
        with file(yaml_filepath, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file)

        return (yaml_content, xml_content)

    def test_yaml_snippet(self):
        yaml_content, expected_xml = self.__read_content()

        xml_project = XML.Element('project')  # root element
        parser = YamlParser()
        pub = general.General(ModuleRegistry({}))

        # Generate the XML tree directly with modules/general
        pub.gen_xml(parser, xml_project, yaml_content)

        # Prettify generated XML
        pretty_xml = XmlJob(xml_project, 'fixturejob').output()

        self.assertThat(
            pretty_xml,
            testtools.matchers.DocTestMatches(expected_xml,
                                              doctest.ELLIPSIS |
                                              doctest.NORMALIZE_WHITESPACE |
                                              doctest.REPORT_NDIFF)
        )
