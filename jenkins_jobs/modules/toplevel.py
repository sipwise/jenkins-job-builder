# Copyright 2012 Hewlett-Packard Development Company, L.P.
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


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base


class TopLevel(jenkins_jobs.modules.base.Base):
    sequence = 1

    def gen_xml(self, parser, xml, data):
        jdk = data.get('jdk', None)
        if jdk:
            XML.SubElement(xml, 'jdk').text = jdk
        XML.SubElement(xml, 'actions')
        description = XML.SubElement(xml, 'description')
        description.text = data.get('description', '')
        XML.SubElement(xml, 'keepDependencies').text = 'false'
        if data.get('disabled'):
            XML.SubElement(xml, 'disabled').text = 'true'
        else:
            XML.SubElement(xml, 'disabled').text = 'false'
        if data.get('block-downstream'):
            XML.SubElement(xml,
                           'blockBuildWhenDownstreamBuilding').text = 'true'
        else:
            XML.SubElement(xml,
                           'blockBuildWhenDownstreamBuilding').text = 'false'
        if data.get('block-upstream'):
            XML.SubElement(xml,
                           'blockBuildWhenUpstreamBuilding').text = 'true'
        else:
            XML.SubElement(xml,
                           'blockBuildWhenUpstreamBuilding').text = 'false'
        if data.get('concurrent'):
            XML.SubElement(xml, 'concurrentBuild').text = 'true'
        else:
            XML.SubElement(xml, 'concurrentBuild').text = 'false'
        if('quiet-period' in data):
            XML.SubElement(xml, 'quietPeriod').text = str(data['quiet-period'])
        node = data.get('node', None)
        if node:
            XML.SubElement(xml, 'assignedNode').text = node
            XML.SubElement(xml, 'canRoam').text = 'false'
