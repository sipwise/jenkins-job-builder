#!/usr/bin/env python
# Copyright (C) 2015 Wayne Warren
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
import logging
import sys
import jenkins_jobs.cli.subcommand.base as base
import jenkins_jobs.utils as utils
from jenkins_jobs.builder import JenkinsManager
from jenkins_jobs.parser import matches
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.registry import ModuleRegistry


def list_duplicates(seq):
    seen = set()
    return set(x for x in seq if x in seen or seen.add(x))


class ListSubCommand(base.BaseSubCommand):

    def parse_args(self, subparser):
        list = subparser.add_parser('list', help="List jobs")

        self.parse_option_recursive_exclude(list)

        list.add_argument('names',
                          help='name(s) of job(s)',
                          nargs='*',
                          default=None)
        list.add_argument('-p', '--path', default=None,
                          help='path to YAML file or directory')

    def execute(self, options, jjb_config):
        self.jjb_config = jjb_config
        self.jenkins = JenkinsManager(jjb_config)

        jobs = self.get_jobs(options.names, options.path)

        logging.info("Matching jobs: %d", len(jobs))
        stdout = utils.wrap_stream(sys.stdout)

        for job in jobs:
            stdout.write((job + '\n').encode('utf-8'))

    def get_jobs(self, jobs_glob=None, fn=None):
        if fn:
            registry = ModuleRegistry(self.jjb_config,
                                      self.jenkins.plugins_list)
            parser = YamlParser(self.jjb_config)
            parser.load_files(fn)
            parser.expandYaml(registry, jobs_glob)
            jobs = [j['name'] for j in parser.jobs]

            # self.load_files(fn)
            # self.parser.expandYaml(jobs_glob)
            # jobs = [j['name'] for j in self.parser.jobs]
        else:
            jobs = [j['name'] for j in self.jenkins.get_jobs()
                    if not jobs_glob or matches(j['name'], jobs_glob)]

        jobs = sorted(jobs)
        for duplicate in list_duplicates(jobs):
            logging.warning("Found duplicate job name '%s', likely bug.",
                            duplicate)

        logging.debug("Builder.get_jobs: returning %r", jobs)

        return jobs
