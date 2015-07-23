# Copyright 2015 Openstack Foundation

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
The view pipeline module handles creating Jenkins Build Pipeline views.
To create a list view specify ``list`` in the ``view-type`` attribute
to the :ref:`View` definition.
Requires the Jenkins
:jenkins-wiki:`Build Pipeline Plugin <build-pipeline-plugin>`.

:View Parameters:
    * **firstJob** (`str`): Parent Job in the view.
    * **noOfDisplayedBuilds** (`str`): Number of builds to display.
      (default 1)
    * **title** (`str`): Build view title. (optional)
    * **linkStyle** (`str`): Console output link style. Can be
      'Lightbox', 'New Window', or 'This Window'. (default Lightbox)
    * **css-Url** (`str`): Url for Custom CSS files (optional)
    * **latest-job-only** (`bool`) Trigger only latest job.
      (default false)
    * **manual-trigger** (`bool`) Always allow manual trigger.
      (default false)
    * **show-parameters** (`bool`) Show pipeline parameters.
      (default false)
    * **parameters-in-headers** (`bool`) Show pipeline parameters in
      headers. (default false)
    * **starts-with-parameters** (`bool`) Use Starts with parameters.
      (default false)
    * **refresh-frequency** (`str`) Frequency to refresh in seconds.
      (default '3')
    * **definition-header** (`bool`) Show pipeline definition header.
      (default false)

Example:

    .. literalinclude::
    /../../tests/view_pipeline/fixtures/pipeline_view001.yaml

Example:

    .. literalinclude::
    /../../tests/view_pipeline/fixtures/pipeline_view002.yaml
"""


import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base_view


class Pipeline(jenkins_jobs.modules.base_view.BaseView):
    sequence = 0

    def root_xml(self, data):
        linktypes = ['Lightbox', 'New Window']
        root = XML.Element('au.com.centrumsystems.hudson.'
                           'plugin.buildpipeline.BuildPipelineView',
                           {'plugin': 'build-pipeline-plugin'})

        root = self.gen_view(data=data, root=root)

        GBurl = ('au.com.centrumsystems.hudson.plugin.buildpipeline.'
                 'DownstreamProjectGridBuilder')
        gridBuilder = XML.SubElement(root, 'gridBuilder', {'class': GBurl})

        jobname = data.get('firstJob', '')
        XML.SubElement(gridBuilder, 'firstJob').text = jobname

        builds = str(data.get('noOfDisplayedBuilds', 1))
        XML.SubElement(root, 'noOfDisplayedBuilds').text = builds

        title = data.get('title', None)
        BVT_element = XML.SubElement(root, 'buildViewTitle')
        if title is not None:
            BVT_element.text = title

        linkStyle = data.get('link-style', 'Lightbox')
        LS_element = XML.SubElement(root, 'consoleOutputLinkStyle')
        if linkStyle in linktypes:
            LS_element.text = linkStyle
        else:
            LS_element.text = 'Lightbox'

        cssUrl = data.get('css-Url', None)
        CU_element = XML.SubElement(root, 'cssUrl')
        if cssUrl is not None:
            CU_element.text = cssUrl

        latest_job_only = data.get('latest-job-only', False)
        OLJ_element = XML.SubElement(root, 'triggerOnlyLatestJob')
        OLJ_element.text = 'true' if latest_job_only else 'false'

        manual_trigger = data.get('manual-trigger', False)
        AMT_element = XML.SubElement(root, 'alwaysAllowManualTrigger')
        AMT_element.text = 'true' if manual_trigger else 'false'

        show_parameters = data.get('show-parameters', False)
        PP_element = XML.SubElement(root, 'showPipelineParameters')
        PP_element.text = 'true' if show_parameters else 'false'

        parameters_in_headers = data.get('parameters-in-headers', False)
        PIH_element = XML.SubElement(root, 'showPipelineParametersInHeaders')
        PIH_element.text = 'true' if parameters_in_headers else 'false'

        start_with_parameters = data.get('start-with-parameters', False)
        SWP_element = XML.SubElement(root, 'startsWithParameters')
        SWP_element.text = 'true' if start_with_parameters else 'false'

        refresh_frequency = str(data.get('refresh-frequency', 3))
        XML.SubElement(root, 'refreshFrequency').text = refresh_frequency

        headers = data.get('definition-header', False)
        DH_element = XML.SubElement(root, 'showPipelineDefinitionHeader')
        DH_element.text = 'true' if headers else 'false'

        return root
