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

from .errors import JenkinsJobsException
from .loc_loader import LocDict
from .root_base import RootBase, NonTemplateRootMixin, TemplateRootMixin, Group
from .defaults import split_contents_params, job_contents_keys


@dataclass
class JobBase(RootBase):
    project_type: str
    folder: str

    @classmethod
    def from_dict(cls, config, roots, expander, data, pos):
        keep_descriptions = config.yamlparser["keep_descriptions"]
        d = data.copy()
        name = d.pop_required_loc_string("name")
        id = d.pop_loc_string("id", None)
        description = d.pop_loc_string("description", None)
        defaults = d.pop_loc_string("defaults", "global")
        project_type = d.pop_loc_string("project-type", None)
        folder = d.pop_loc_string("folder", None)
        contents, params = split_contents_params(d, job_contents_keys)
        return cls(
            roots.defaults,
            expander,
            keep_descriptions,
            id,
            name,
            pos,
            description,
            defaults,
            params,
            contents,
            project_type,
            folder,
        )

    def _as_dict(self):
        data = LocDict.merge(
            {"name": self._full_name},
            self.contents,
        )
        if self.project_type:
            data["project-type"] = self.project_type
        return data

    @property
    def _full_name(self):
        if self.folder:
            return f"{self.folder}/{self.name}"
        else:
            return self.name


class Job(JobBase, NonTemplateRootMixin):
    @classmethod
    def add(cls, config, roots, expander, param_expander, data, pos):
        job = cls.from_dict(config, roots, expander, data, pos)
        roots.assign(roots.jobs, job.id, job, "job")

    def __str__(self):
        return f"job {self.name!r}"


class JobTemplate(JobBase, TemplateRootMixin):
    @classmethod
    def add(cls, config, roots, expander, params_expander, data, pos):
        template = cls.from_dict(config, roots, params_expander, data, pos)
        roots.assign(roots.job_templates, template.id, template, "job template")

    def __str__(self):
        return f"job template {self.name!r}"


@dataclass
class JobGroup(Group):
    _jobs: dict
    _job_templates: dict

    @classmethod
    def add(cls, config, roots, expander, params_expander, data, pos):
        d = data.copy()
        name = d.pop_required_loc_string("name")
        try:
            job_specs = cls._specs_from_list(d.pop("jobs", None))
        except JenkinsJobsException as x:
            raise x.with_context(f"In job {name!r}", pos=pos)
        group = cls(
            name,
            pos,
            job_specs,
            d,
            roots.jobs,
            roots.job_templates,
        )
        roots.assign(roots.job_groups, group.name, group, "job group")

    def __str__(self):
        return f"job group {self.name!r}"

    @property
    def _root_dicts(self):
        return [self._jobs, self._job_templates]
