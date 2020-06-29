# Copyright 2020 Liberty Global B.V.
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
from jenkins_jobs.local_yaml import Jinja2Loader


class PipelineDSL(jenkins_jobs.modules.base.Base):
    sequence = 60

    component_type = "pipeline-dsl"

    def gen_xml(self, xml_parent, data):
        if data.get("project-type") != "pipeline" or data.get("dsl") is None:
            return
        pipeline_definition = xml_parent.find("definition")
        if isinstance(data.get("dsl"), Jinja2Loader):
            self.registry.dispatch(
                "pipeline-dsl", pipeline_definition, {"dsl": data["dsl"]}, data
            )
        else:
            XML.SubElement(pipeline_definition, "script").text = data["dsl"]


def dsl(registry, xml_parent, data):
    """yaml: dsl
    """
    XML.SubElement(xml_parent, "script").text = data
