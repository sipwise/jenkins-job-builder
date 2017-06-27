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


"""
This file is responsible for the general xml definitions for promoted-builds.
The documentation foe promoted-builds arguments is in the promoted_build
function in properties.py because the user will define all their promoted-build
yaml in that module.
"""

import xml.etree.ElementTree as XML

import jenkins_jobs.modules.base
import jenkins_jobs.modules.helpers as helpers


class PromotedBuilds(jenkins_jobs.modules.base.Base):
    sequence = 0

    component_type = 'promoted_builds'
    component_list_type = 'promoted_builds'

    def root_xml(self, data):
        xml_parent = XML.Element(
            'hudson.plugins.promoted__builds.PromotionProcess')

        XML.SubElement(xml_parent, 'keepDependencies').text = 'false'

        return xml_parent


class PromotedBuildsGeneral(jenkins_jobs.modules.base.Base):
    sequence = 30

    component_type = 'promoted_builds_general'
    component_list_type = 'promoted_builds_general'

    def gen_xml(self, xml, data):

        XML.SubElement(xml, 'canRoam').text = 'false'
        XML.SubElement(xml, 'disabled').text = 'false'
        XML.SubElement(xml, 'blockBuildWhenDownstreamBuilding').text = 'false'
        XML.SubElement(xml, 'blockBuildWhenUpstreamBuilding').text = 'false'
        XML.SubElement(xml, 'triggers')
        XML.SubElement(xml, 'concurrentBuild').text = 'false'

        if 'conditions' in data:
            conditions = xml.find('conditions')
            if conditions is None:
                conditions = XML.SubElement(xml, 'conditions')
            for condition in data.get('conditions', []):
                self.registry.dispatch(
                    'promoted_builds_general', conditions, condition)

        mapping = [
            ('icon', 'icon', 'star-gold'),
            ('node', 'assignedLabel', None),
            ('visible', 'isVisible', '')
        ]
        helpers.convert_mapping_to_xml(xml, data, mapping, fail_required=False)


def condition_manual(registry, xml_parent, data):
    """yaml: manual

    This function is responsible for generating manual condition xml in
    promoted-builds, the arguments are documented in promoted_build in
    properties.py
    """

    xml_manual = XML.SubElement(xml_parent,
        'hudson.plugins.promoted__builds.conditions.ManualCondition')

    XML.SubElement(xml_manual, 'users').text = ','.join(data.get('users', []))

    parameter_defs = xml_manual.find('parameters')
    if parameter_defs is None:
        parameter_defs = XML.SubElement(xml_manual, 'parameterDefinitions')
    for param in data.get('parameters', []):
        registry.dispatch('parameter', parameter_defs, param)


def condition_immediate(registry, xml_parent, data):
    """yaml: immediate

    This function is responsible for generating immediate condition xml in
    promoted-builds, the arguments are documented in promoted_build in
    properties.py
    """

    xml_immediate = XML.SubElement(
        xml_parent, 'hudson.plugins.promoted__builds.'
                    'conditions.SelfPromotionCondition')

    mapping = [('even-if-unstable', 'evenIfUnstable', False)]
    helpers.convert_mapping_to_xml(xml_immediate, data, mapping,
                                   fail_required=True)


def condition_perameter(registry, xml_parent, data):
    """yaml: parameter

    This function is responsible for generating parameter condition xml in
    promoted-builds, the arguments are documented in promoted_build in
    properties.py
    """

    xml_parameter = XML.SubElement(
        xml_parent, 'hudson.plugins.promoted__builds.conditions.'
                    'ParameterizedSelfPromotionCondition')

    mapping = [
        ('even-if-unstable', 'evenIfUnstable', False),
        ('name', 'parameterName', ''),
        ('value', 'parameterValue', '')
    ]
    helpers.convert_mapping_to_xml(xml_parameter, data, mapping,
                                   fail_required=True)


def condition_downstream(registry, xml_parent, data):
    """yaml: downstream

    This function is responsible for generating downstream condition xml in
    promoted-builds, the arguments are documented in promoted_build in
    properties.py
    """

    xml_downstream = XML.SubElement(
        xml_parent, 'hudson.plugins.promoted__builds.conditions.'
                    'DownstreamPassCondition')
    XML.SubElement(xml_downstream, 'jobs').text = \
        ','.join(data.get('jobs', []))

    mapping = [('even-if-unstable', 'evenIfUnstable', False)]
    helpers.convert_mapping_to_xml(xml_downstream, data, mapping,
                                   fail_required=True)


def condition_upstream(registry, xml_parent, data):
    """yaml: upstream

    This function is responsible for generating upstream condition xml in
    promoted-builds, the arguments are documented in promoted_build in
    properties.py
    """

    xml_upstream = XML.SubElement(
        xml_parent, 'hudson.plugins.promoted__builds.conditions.'
                    'UpstreamPromotionCondition')

    XML.SubElement(xml_upstream, 'requiredPromotionNames').text = \
        ','.join(data.get('jobs', []))
