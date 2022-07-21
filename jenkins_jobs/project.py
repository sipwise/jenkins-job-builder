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

from dataclasses import dataclass

from .root_base import GroupBase


@dataclass
class Project(GroupBase):
    _jobs: dict
    _job_templates: dict
    _job_groups: dict
    _views: dict
    _view_templates: dict
    _view_groups: dict
    name: str
    defaults_name: str
    job_specs: list  # list[Spec]
    view_specs: list  # list[Spec]
    params: dict

    @classmethod
    def add(cls, config, roots, expander, params_expander, data):
        d = {**data}
        name = d.pop("name")
        defaults = d.pop("defaults", None)
        job_specs = [
            cls._spec_from_dict(item, error_context=f"Project {name}")
            for item in d.pop("jobs", [])
        ]
        view_specs = [
            cls._spec_from_dict(item, error_context=f"Project {name}")
            for item in d.pop("views", [])
        ]
        project = cls(
            roots.jobs,
            roots.job_templates,
            roots.job_groups,
            roots.views,
            roots.view_templates,
            roots.view_groups,
            name,
            defaults,
            job_specs,
            view_specs,
            params=d,
        )
        roots.assign(roots.projects, project.name, project, "project")

    def __str__(self):
        return f"Project {self.name}"

    @property
    def _my_params(self):
        return {"name": self.name}

    def generate_jobs(self):
        root_dicts = [self._jobs, self._job_templates, self._job_groups]
        return self._generate_items(
            root_dicts, self.job_specs, self.defaults_name, params={}
        )

    def generate_views(self):
        root_dicts = [self._views, self._view_templates, self._view_groups]
        return self._generate_items(
            root_dicts, self.view_specs, self.defaults_name, params={}
        )
