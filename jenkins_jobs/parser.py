#!/usr/bin/env python
# Copyright (C) 2015 OpenStack, LLC.
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

# Manage JJB yaml feature implementation

import copy
import fnmatch
import itertools
import logging
import pkg_resources

import jenkins_jobs.local_yaml as local_yaml
from jenkins_jobs.constants import MAGIC_MANAGE_STRING
from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.registry import ModuleRegistry
from jenkins_jobs.formatter import deep_format
from jenkins_jobs.xml_config import XmlJob

logger = logging.getLogger(__name__)


def matches(what, glob_patterns):
    """
    Checks if the given string, ``what``, matches any of the glob patterns in
    the iterable, ``glob_patterns``

    :arg str what: String that we want to test if it matches a pattern
    :arg iterable glob_patterns: glob patterns to match (list, tuple, set,
    etc.)
    """
    return any(fnmatch.fnmatch(what, glob_pattern)
               for glob_pattern in glob_patterns)


class YamlParser(object):
    def __init__(self, config=None, plugins_info=None):
        self.data = {}
        self.jobs = []
        self.xml_jobs = []
        self.config = config
        self.registry = ModuleRegistry(self.config, plugins_info)
        self.path = ["."]
        if self.config:
            if config.has_section('job_builder') and \
                    config.has_option('job_builder', 'include_path'):
                self.path = config.get('job_builder',
                                       'include_path').split(':')
        self.keep_desc = self.get_keep_desc()
        self.merge_defaults = self.get_merge_defaults()

    def get_keep_desc(self):
        keep_desc = False
        if self.config and self.config.has_section('job_builder') and \
                self.config.has_option('job_builder', 'keep_descriptions'):
            keep_desc = self.config.getboolean('job_builder',
                                               'keep_descriptions')
        return keep_desc

    def get_merge_defaults(self):
        merge_defaults = False
        if self.config and self.config.has_section('job_builder') and \
                self.config.has_option('job_builder', 'merge_defaults'):
            merge_defaults = self.config.getboolean('job_builder',
                                                    'merge_defaults')
        return merge_defaults

    def parse_fp(self, fp):
        data = local_yaml.load(fp, search_path=self.path)
        if data:
            if not isinstance(data, list):
                raise JenkinsJobsException(
                    "The topmost collection in file '{fname}' must be a list,"
                    " not a {cls}".format(fname=getattr(fp, 'name', fp),
                                          cls=type(data)))
            for item in data:
                cls, dfn = next(iter(item.items()))
                group = self.data.get(cls, {})
                if len(item.items()) > 1:
                    n = None
                    for k, v in item.items():
                        if k == "name":
                            n = v
                            break
                    # Syntax error
                    raise JenkinsJobsException("Syntax error, for item "
                                               "named '{0}'. Missing indent?"
                                               .format(n))
                name = dfn['name']
                if name in group:
                    self._handle_dups("Duplicate entry found in '{0}: '{1}' "
                                      "already defined".format(fp.name, name))
                group[name] = dfn
                self.data[cls] = group

    def parse(self, fn):
        with open(fn) as fp:
            self.parse_fp(fp)

    def _handle_dups(self, message):

        if not (self.config and self.config.has_section('job_builder') and
                self.config.getboolean('job_builder', 'allow_duplicates')):
            logger.error(message)
            raise JenkinsJobsException(message)
        else:
            logger.warn(message)

    def getJob(self, name):
        job = self.data.get('job', {}).get(name, None)
        if not job:
            return job
        return self.applyDefaults(job)

    def getJobGroup(self, name):
        return self.data.get('job-group', {}).get(name, None)

    def getJobTemplate(self, name):
        job = self.data.get('job-template', {}).get(name, None)
        if not job:
            return job
        return self.applyDefaults(job)

    def applyDefaults(self, data, override_dict=None):
        if override_dict is None:
            override_dict = {}

        whichdefaults = data.get('defaults', 'global')
        defaults = copy.deepcopy(self.data.get('defaults',
                                 {}).get(whichdefaults, {}))
        if defaults == {} and whichdefaults != 'global':
            raise JenkinsJobsException("Unknown defaults set: '{0}'"
                                       .format(whichdefaults))

        for key in override_dict.keys():
            if key in defaults.keys():
                defaults[key] = override_dict[key]

        newdata = {}
        newdata.update(defaults)

        if self.merge_defaults:
            if newdata == {}:
                newdata.update(data)
            else:
                self.deepUpdate(newdata, data)
        else:
            newdata.update(data)
        return newdata

    def deepUpdate(self, data, updated_data):
        if hasattr(data, 'format') or hasattr(updated_data, 'format'):
            return None

        common_keys = self._findCommonKey(data, updated_data)
        for common_key in common_keys:
            self._deepUpdate(common_key, data, updated_data)

        diff_keys = self._findDiffKey(data, updated_data)
        for diff_key in diff_keys:
            data[diff_key] = updated_data[diff_key]

    def _deepUpdate(self, common_key, data, updated_data):
        attr = data[common_key]
        updated_attr = updated_data[common_key]

        if hasattr(attr, 'format') and hasattr(updated_attr, 'format'):
            data[common_key] = updated_attr
            return None

        if hasattr(attr, 'keys'):
            self.deepUpdate(attr, updated_attr)
            return None

        if hasattr(attr, '__iter__'):
            for ele in updated_attr:
                if hasattr(ele, 'format') and ele not in attr:
                    attr.append(ele)
                if hasattr(ele, 'keys'):
                    for od in attr:
                        if hasattr(od, 'keys') and \
                                self._findCommonKey(od, ele):
                            self.deepUpdate(od, ele)
                            break
                    else:
                        attr.append(ele)
            return None

        return None

    def _findCommonKey(self, data, updated_data):
        return list(set(data.keys()).intersection(set(updated_data.keys())))

    def _findDiffKey(self, data, updated_data):
        return list(set(updated_data.keys()).difference(set(data.keys())))

    def formatDescription(self, job):
        if self.keep_desc:
            description = job.get("description", None)
        else:
            description = job.get("description", '')
        if description is not None:
            job["description"] = description + \
                self.get_managed_string().lstrip()

    def expandYaml(self, jobs_glob=None):
        changed = True
        while changed:
            changed = False
            for module in self.registry.modules:
                if hasattr(module, 'handle_data'):
                    if module.handle_data(self):
                        changed = True

        for job in self.data.get('job', {}).values():
            if jobs_glob and not matches(job['name'], jobs_glob):
                logger.debug("Ignoring job {0}".format(job['name']))
                continue
            logger.debug("Expanding job '{0}'".format(job['name']))
            job = self.applyDefaults(job)
            self.formatDescription(job)
            self.jobs.append(job)
        for project in self.data.get('project', {}).values():
            logger.debug("Expanding project '{0}'".format(project['name']))
            # use a set to check for duplicate job references in projects
            seen = set()
            for jobspec in project.get('jobs', []):
                if isinstance(jobspec, dict):
                    # Singleton dict containing dict of job-specific params
                    jobname, jobparams = next(iter(jobspec.items()))
                    if not isinstance(jobparams, dict):
                        jobparams = {}
                else:
                    jobname = jobspec
                    jobparams = {}
                job = self.getJob(jobname)
                if job:
                    # Just naming an existing defined job
                    if jobname in seen:
                        self._handle_dups("Duplicate job '{0}' specified "
                                          "for project '{1}'".format(
                                              jobname, project['name']))
                    seen.add(jobname)
                    continue
                # see if it's a job group
                group = self.getJobGroup(jobname)
                if group:
                    for group_jobspec in group['jobs']:
                        if isinstance(group_jobspec, dict):
                            group_jobname, group_jobparams = \
                                next(iter(group_jobspec.items()))
                            if not isinstance(group_jobparams, dict):
                                group_jobparams = {}
                        else:
                            group_jobname = group_jobspec
                            group_jobparams = {}
                        job = self.getJob(group_jobname)
                        if job:
                            if group_jobname in seen:
                                self._handle_dups(
                                    "Duplicate job '{0}' specified for "
                                    "project '{1}'".format(group_jobname,
                                                           project['name']))
                            seen.add(group_jobname)
                            continue
                        template = self.getJobTemplate(group_jobname)
                        # Allow a group to override parameters set by a project
                        d = {}
                        d.update(project)
                        d.update(jobparams)
                        d.update(group)
                        d.update(group_jobparams)
                        # Except name, since the group's name is not useful
                        d['name'] = project['name']
                        if template:
                            self.expandYamlForTemplateJob(d, template,
                                                          jobs_glob)
                    continue
                # see if it's a template
                template = self.getJobTemplate(jobname)
                if template:
                    d = {}
                    d.update(project)
                    d.update(jobparams)
                    self.expandYamlForTemplateJob(d, template, jobs_glob)
                else:
                    raise JenkinsJobsException("Failed to find suitable "
                                               "template named '{0}'"
                                               .format(jobname))
        # check for duplicate generated jobs
        seen = set()
        # walk the list in reverse so that last definition wins
        for job in self.jobs[::-1]:
            if job['name'] in seen:
                self._handle_dups("Duplicate definitions for job '{0}' "
                                  "specified".format(job['name']))
                self.jobs.remove(job)
            seen.add(job['name'])

    def expandYamlForTemplateJob(self, project, template, jobs_glob=None):
        dimensions = []
        template_name = template['name']
        # reject keys that are not useful during yaml expansion
        for k in ['jobs']:
            project.pop(k)
        for (k, v) in project.items():
            tmpk = '{{{0}}}'.format(k)
            if tmpk not in template_name:
                logger.debug("Variable %s not in name %s, rejecting from job"
                             " matrix expansion.", tmpk, template_name)
                continue
            if type(v) == list:
                dimensions.append(zip([k] * len(v), v))
        # XXX somewhat hackish to ensure we actually have a single
        # pass through the loop
        if len(dimensions) == 0:
            dimensions = [(("", ""),)]

        for values in itertools.product(*dimensions):
            params = copy.deepcopy(project)
            params = self.applyDefaults(params, template)

            expanded_values = {}
            for (k, v) in values:
                if isinstance(v, dict):
                    inner_key = next(iter(v))
                    expanded_values[k] = inner_key
                    expanded_values.update(v[inner_key])
                else:
                    expanded_values[k] = v

            params.update(expanded_values)
            params = deep_format(params, params)
            allow_empty_variables = self.config \
                and self.config.has_section('job_builder') \
                and self.config.has_option(
                    'job_builder', 'allow_empty_variables') \
                and self.config.getboolean(
                    'job_builder', 'allow_empty_variables')

            for key in template.keys():
                if key not in params:
                    params[key] = template[key]

            expanded = deep_format(template, params, allow_empty_variables)

            job_name = expanded.get('name')
            if jobs_glob and not matches(job_name, jobs_glob):
                continue

            self.formatDescription(expanded)
            self.jobs.append(expanded)

    def get_managed_string(self):
        # The \n\n is not hard coded, because they get stripped if the
        # project does not otherwise have a description.
        return "\n\n" + MAGIC_MANAGE_STRING

    def generateXML(self):
        for job in self.jobs:
            self.xml_jobs.append(self.getXMLForJob(job))

    def getXMLForJob(self, data):
        kind = data.get('project-type', 'freestyle')

        for ep in pkg_resources.iter_entry_points(
                group='jenkins_jobs.projects', name=kind):
            Mod = ep.load()
            mod = Mod(self.registry)
            xml = mod.root_xml(data)
            self.gen_xml(xml, data)
            job = XmlJob(xml, data['name'])
            return job

    def gen_xml(self, xml, data):
        for module in self.registry.modules:
            if hasattr(module, 'gen_xml'):
                module.gen_xml(self, xml, data)
