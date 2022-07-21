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

import logging
from collections import defaultdict

from .errors import JenkinsJobsException
from .defaults import Defaults
from .job import Job, JobTemplate, JobGroup
from .view import View, ViewTemplate, ViewGroup
from .project import Project
from .macro import macro_adders

logger = logging.getLogger(__name__)


root_adders = {
    "defaults": Defaults.add,
    "job": Job.add,
    "job-template": JobTemplate.add,
    "job-group": JobGroup.add,
    "view": View.add,
    "view-template": ViewTemplate.add,
    "view-group": ViewGroup.add,
    "project": Project.add,
    **macro_adders,
}


class Roots:
    """Container for root YAML elements - jobs, views, templates, projects and macros"""

    def __init__(self, config):
        self._allow_duplicates = config.yamlparser["allow_duplicates"]
        self.defaults = {}
        self.jobs = {}
        self.job_templates = {}
        self.job_groups = {}
        self.views = {}
        self.view_templates = {}
        self.view_groups = {}
        self.projects = {}
        self.macros = defaultdict(dict)  # type -> name -> Macro

    def generate_jobs(self):
        expanded_jobs = []
        for job in self.jobs.values():
            expanded_jobs += job.top_level_generate_items()
        for project in self.projects.values():
            expanded_jobs += project.generate_jobs()
        return self._remove_duplicates(expanded_jobs)

    def generate_views(self):
        expanded_views = []
        for view in self.views.values():
            expanded_views += view.top_level_generate_items()
        for project in self.projects.values():
            expanded_views += project.generate_views()
        return self._remove_duplicates(expanded_views)

    def assign(self, container, id, value, title):
        if id in container:
            self._handle_dups(f"Duplicate {title}: {id}")
        container[id] = value

    def _remove_duplicates(self, job_list):
        seen = set()
        unique_list = []
        # Last definition wins.
        for job in reversed(job_list):
            name = job["name"]
            if name in seen:
                self._handle_dups(
                    f"Duplicate definitions for job {name!r} specified",
                )
            else:
                unique_list.append(job)
                seen.add(name)
        return unique_list[::-1]

    def _handle_dups(self, message):
        if self._allow_duplicates:
            logger.warning(message)
        else:
            logger.error(message)
            raise JenkinsJobsException(message)
