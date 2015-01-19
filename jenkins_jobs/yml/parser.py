#!/usr/bin/env python
# Copyright (C) 2012 OpenStack, LLC.
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

# Parse and expand yaml for JJB

import hashlib
import json
import logging
import copy
import itertools
import re
import os
from pprint import pformat

import six

from jenkins_jobs.errors import JenkinsJobsException
from jenkins_jobs.utils import matches
import jenkins_jobs.local_yaml as local_yaml


logger = logging.getLogger(__name__)
MAGIC_MANAGE_STRING = "<!-- Managed by Jenkins Job Builder -->"


def deep_format(obj, paramdict):
    """Apply the paramdict via str.format() to all string objects found within
       the supplied obj. Lists and dicts are traversed recursively."""
    # YAML serialisation was originally used to achieve this, but that places
    # limitations on the values in paramdict - the post-format result must
    # still be valid YAML (so substituting-in a string containing quotes, for
    # example, is problematic).
    if hasattr(obj, 'format'):
        try:
            result = re.match('^{obj:(?P<key>\w+)}$', obj)
            if result is not None:
                ret = paramdict[result.group("key")]
            else:
                ret = obj.format(**paramdict)
        except KeyError as exc:
            missing_key = exc.message
            desc = "%s parameter missing to format %s\nGiven:\n%s" % (
                   missing_key, obj, pformat(paramdict))
            raise JenkinsJobsException(desc)
    elif isinstance(obj, list):
        ret = []
        for item in obj:
            ret.append(deep_format(item, paramdict))
    elif isinstance(obj, dict):
        ret = {}
        for item in obj:
            try:
                ret[item.format(**paramdict)] = \
                    deep_format(obj[item], paramdict)
            except KeyError as exc:
                missing_key = exc.message
                desc = "%s parameter missing to format %s\nGiven:\n%s" % (
                    missing_key, obj, pformat(paramdict))
                raise JenkinsJobsException(desc)
    else:
        ret = obj
    return ret


class YamlParser(object):
    def __init__(self, config=None):
        self.data = {}
        self.jobs = []
        self.config = config
        self.path = ["."]
        if self.config:
            if config.has_section('job_builder') and \
                    config.has_option('job_builder', 'include_path'):
                self.path = config.get('job_builder',
                                       'include_path').split(':')
        self.keep_desc = self._get_keep_desc()

    def _get_keep_desc(self):
        keep_desc = False
        if self.config and self.config.has_section('job_builder') and \
                self.config.has_option('job_builder', 'keep_descriptions'):
            keep_desc = self.config.getboolean('job_builder',
                                               'keep_descriptions')
        return keep_desc

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
                    self._handle_dups("Duplicate entry found: '{0}' is "
                                      "already defined".format(name))
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

    def _getJob(self, name):
        job = self.data.get('job', {}).get(name, None)
        if not job:
            return job
        return self._applyDefaults(job)

    def _getJobGroup(self, name):
        return self.data.get('job-group', {}).get(name, None)

    def _getJobTemplate(self, name):
        job = self.data.get('job-template', {}).get(name, None)
        if not job:
            return job
        return self._applyDefaults(job)

    def _applyDefaults(self, data):
        whichdefaults = data.get('defaults', 'global')
        defaults = self.data.get('defaults', {}).get(whichdefaults, {})
        if defaults == {} and whichdefaults != 'global':
            raise JenkinsJobsException("Unknown defaults set: '{0}'"
                                       .format(whichdefaults))
        newdata = {}
        newdata.update(defaults)
        newdata.update(data)
        return newdata

    def _formatDescription(self, job):
        if self.keep_desc:
            description = job.get("description", None)
        else:
            description = job.get("description", '')
        if description is not None:
            job["description"] = description + \
                self._get_managed_string().lstrip()

    def expandYaml(self, registry, jobs_filter=None):
        changed = True
        while changed:
            changed = False
            for module in registry.modules:
                if hasattr(module, 'handle_data'):
                    if module.handle_data(self):
                        changed = True

        for job in self.data.get('job', {}).values():
            if jobs_filter and not matches(job['name'], jobs_filter):
                logger.debug("Ignoring job {0}".format(job['name']))
                continue
            logger.debug("Expanding job '{0}'".format(job['name']))
            job = self._applyDefaults(job)
            self._formatDescription(job)
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
                job = self._getJob(jobname)
                if job:
                    # Just naming an existing defined job
                    if jobname in seen:
                        self._handle_dups("Duplicate job '{0}' specified "
                                          "for project '{1}'".format(
                                              jobname, project['name']))
                    seen.add(jobname)
                    continue
                # see if it's a job group
                group = self._getJobGroup(jobname)
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
                        job = self._getJob(group_jobname)
                        if job:
                            if group_jobname in seen:
                                self._handle_dups(
                                    "Duplicate job '{0}' specified for "
                                    "project '{1}'".format(group_jobname,
                                                           project['name']))
                            seen.add(group_jobname)
                            continue
                        template = self._getJobTemplate(group_jobname)
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
                                                          jobs_filter)
                    continue
                # see if it's a template
                template = self._getJobTemplate(jobname)
                if template:
                    d = {}
                    d.update(project)
                    d.update(jobparams)
                    self.expandYamlForTemplateJob(d, template, jobs_filter)
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

    def expandYamlForTemplateJob(self, project, template, jobs_filter=None):
        dimensions = []
        for (k, v) in project.items():
            if type(v) == list and k not in ['jobs']:
                dimensions.append(zip([k] * len(v), v))
        # XXX somewhat hackish to ensure we actually have a single
        # pass through the loop
        if len(dimensions) == 0:
            dimensions = [(("", ""),)]
        checksums = set([])
        for values in itertools.product(*dimensions):
            params = copy.deepcopy(project)
            params = self._applyDefaults(params)

            expanded_values = {}
            for (k, v) in values:
                if isinstance(v, dict):
                    inner_key = next(iter(v))
                    expanded_values[k] = inner_key
                    expanded_values.update(v[inner_key])
                else:
                    expanded_values[k] = v

            params.update(expanded_values)
            expanded = deep_format(template, params)

            # Keep track of the resulting expansions to avoid
            # regenerating the exact same job.  Whenever a project has
            # different values for a parameter and that parameter is not
            # used in the template, we ended up regenerating the exact
            # same job.
            # To achieve that we serialize the expanded template making
            # sure the dict keys are always in the same order. Then we
            # record the checksum in an unordered unique set which let
            # us guarantee a group of parameters will not be added a
            # second time.
            uniq = json.dumps(expanded, sort_keys=True)
            if six.PY3:
                uniq = uniq.encode('utf-8')
            checksum = hashlib.md5(uniq).hexdigest()

            # Lookup the checksum
            if checksum not in checksums:
                # We also want to skip expansion whenever the user did
                # not ask for that job.
                job_name = expanded.get('name')
                if jobs_filter and not matches(job_name, jobs_filter):
                    continue

                self._formatDescription(expanded)
                self.jobs.append(expanded)
                checksums.add(checksum)

    def _get_managed_string(self):
        # The \n\n is not hard coded, because they get stripped if the
        # project does not otherwise have a description.
        return "\n\n" + MAGIC_MANAGE_STRING

    def load_files(self, file_list):
        """
        Given a list of paths, load and parse all yaml files in each path.
        """

        # handle deprecated behavior
        if not hasattr(file_list, '__iter__'):
            logger.warning(
                'Passing single elements for the `file_list` argument in '
                'Builder.load_files is deprecated. Please update your code '
                'to use a list as support for automatic conversion will be '
                'removed in a future version.')
            file_list = [file_list]

        files_to_process = []
        for path in file_list:
            if os.path.isdir(path):
                files_to_process.extend([os.path.join(path, f)
                                         for f in os.listdir(path)
                                         if (f.endswith('.yml')
                                             or f.endswith('.yaml'))])
            else:
                files_to_process.append(path)

        for in_file in files_to_process:
            # use of ask-for-permissions instead of ask-for-forgiveness
            # performs better when low use cases.
            if hasattr(in_file, 'name'):
                fname = in_file.name
            else:
                fname = in_file
            logger.debug("Parsing YAML file {0}".format(fname))
            if hasattr(in_file, 'read'):
                self.parse_fp(in_file)
            else:
                self.parse(in_file)
