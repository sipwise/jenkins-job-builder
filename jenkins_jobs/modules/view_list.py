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
The view list module handles creating Jenkins List views.

To create a list view specify ``list`` in the ``view-type`` attribute
to the :ref:`view_list` definition.

:View Parameters:
    * **name** (`str`): The name of the view.
    * **view-type** (`str`): The type of view.
    * **description** (`str`): A description of the view. (default '')
    * **filter-executors** (`bool`): Show only executors that can
      execute the included views. (default false)
    * **filter-queue** (`bool`): Show only included jobs in builder
      queue. (default false)
    * **job-name** (`list`): List of jobs to be included.
    * **job-filters** (`dict`): Job filters to be included.
            :most-recent: * **max-to-include** (`int`): Maximum number of jobs
                            to include. (default 0)
                          * **check-start-time** (`bool`): Check job start time
                            (default false)
    * **columns** (`list`): List of columns to be shown in view.
    * **regex** (`str`): . Regular expression for selecting jobs
      (optional)
    * **recurse** (`bool`): Recurse in subfolders.(default false)
    * **status-filter** (`bool`): Filter job list by enabled/disabled
      status. (optional)

Example:

    .. literalinclude::
        /../../tests/views/fixtures/view_list001.yaml

Example:

    .. literalinclude::
        /../../tests/views/fixtures/view_list002.yaml
"""

import logging
import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base

from jenkins_jobs.modules.helpers import convert_mapping_to_xml

logger = logging.getLogger(__name__)

COLUMN_DICT = {
    'status': 'hudson.views.StatusColumn',
    'weather': 'hudson.views.WeatherColumn',
    'job': 'hudson.views.JobColumn',
    'last-success': 'hudson.views.LastSuccessColumn',
    'last-failure': 'hudson.views.LastFailureColumn',
    'last-duration': 'hudson.views.LastDurationColumn',
    'build-button': 'hudson.views.BuildButtonColumn',
    'last-stable': 'hudson.views.LastStableColumn',
}
DEFAULT_COLUMNS = ['status', 'weather', 'job', 'last-success', 'last-failure',
                   'last-duration', 'build-button']

JOB_FILTERS = ['most-recent']

class List(jenkins_jobs.modules.base.Base):
    sequence = 0

    def root_xml(self, data):
        root = XML.Element('hudson.model.ListView')

        mapping = [
            ('name', 'name', None),
            ('description', 'description', ''),
            ('filter-executors', 'filterExecutors', False),
            ('filter-queue', 'filterQueue', False)]
        convert_mapping_to_xml(root, data, mapping, fail_required=True)

        XML.SubElement(root, 'properties',
                       {'class': 'hudson.model.View$PropertyList'})

        jn_xml = XML.SubElement(root, 'jobNames')
        jobnames = data.get('job-name', None)
        XML.SubElement(jn_xml, 'comparator', {'class':
                       'hudson.util.CaseInsensitiveComparator'})
        if jobnames is not None:
            for jobname in jobnames:
                XML.SubElement(jn_xml, 'string').text = str(jobname)

        job_filter_xml = XML.SubElement(root, 'jobFilters')
        jobfilters = data.get('job-filters', [])

        if jobfilters is not None:
            logger.debug("jobfilters list: {0}".format(jobfilters))

        # for jobfilter in jobfilters:
        #     if 'most-recent' in jobfilter:
        #         logger.debug("jobfilter list 2: {0}".format(jobfilter))
        #         mr_xml = XML.SubElement(job_filter_xml,
        #                                'hudson.views.MostRecentJobsFilter')
        #         mr_xml.set('plugin', 'view-job-filters')
        #         most_recent = jobfilter['most-recent']
        #         if most_recent['max-to-include']:
        #             XML.SubElement(mr_xml, 'maxToInclude').text = str(most_recent['max-to-include'])
        #         if most_recent['check-start-time']:
        #             XML.SubElement(mr_xml, 'checkStartTime').text = str(most_recent['check-start-time'])

        for jobfilter in jobfilters:
            if 'most-recent' in jobfilter:
                mr_xml = XML.SubElement(job_filter_xml,
                                       'hudson.views.MostRecentJobsFilter')
                mr_xml.set('plugin', 'view-job-filter')
                mapping = [
                    ('max-to-include', 'maxToInclude', '0'),
                    ('check-start-time', 'checkStartTime', False)]
                convert_mapping_to_xml(mr_xml, data, mapping, fail_required=True)

        c_xml = XML.SubElement(root, 'columns')
        columns = data.get('columns', DEFAULT_COLUMNS)

        for column in columns:
            if column in COLUMN_DICT:
                XML.SubElement(c_xml, COLUMN_DICT[column])
        mapping = [
            ('regex', 'includeRegex', None),
            ('recurse', 'recurse', False),
            ('status-filter', 'statusFilter', None)]

        convert_mapping_to_xml(root, data, mapping, fail_required=False)

        return root
