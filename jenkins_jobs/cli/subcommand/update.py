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
import time

from jenkins_jobs.builder import Builder
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.registry import ModuleRegistry
from jenkins_jobs.errors import JenkinsJobsException
import jenkins_jobs.cli.subcommand.base as base


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UpdateSubCommand(base.BaseSubCommand):

    def parse_arg_path(self, parser):
        parser.add_argument('path',
                            help='''colon-separated list of paths to YAML files
                            or directories''',
                            nargs='?',
                            default=sys.stdin)

    def parse_arg_names(self, parser):
        parser.add_argument('names',
                            help='name(s) of job(s)', nargs='*')

    def parse_args(self, subparser):
        update = subparser.add_parser('update')

        self.parse_option_recursive(update)
        self.parse_option_exclude(update)

        self.parse_arg_path(update)
        self.parse_arg_names(update)

        update.add_argument('--delete-old',
                            help='delete obsolete jobs',
                            action='store_true',
                            dest='delete_old',
                            default=False,)
        update.add_argument('--workers',
                            help='''number of workers to use, 0 for
                            autodetection and 1 for just one worker.''',
                            dest='n_workers',
                            type=int,
                            default=1)

    def _generate_xmljobs(self, jjb_config=None):
        options = jjb_config.arguments
        builder = Builder(jjb_config)

        logger.info("Updating jobs in {0} ({1})".format(
            options.path, options.names))
        orig = time.time()

        # Generate XML
        parser = YamlParser(jjb_config)
        registry = ModuleRegistry(jjb_config, builder.plugins_list)

        parser.load_files(options.path)
        registry.set_parser_data(parser.data)

        parser.expandYaml(registry, options.names)
        parser.generateXML(registry)

        jobs = parser.jobs
        step = time.time()
        logging.debug('%d XML files generated in %ss',
                      len(jobs), str(step - orig))

        return builder, parser.xml_jobs

    def execute(self, jjb_config):
        options = jjb_config.arguments

        if options.n_workers < 0:
            raise JenkinsJobsException(
                'Number of workers must be equal or greater than 0')

        builder, xml_jobs = self._generate_xmljobs(jjb_config)

        jobs, num_updated_jobs = builder.update_jobs(
            xml_jobs,
            n_workers=options.n_workers)
        logger.info("Number of jobs updated: %d", num_updated_jobs)

        if options.delete_old:
            n = builder.delete_old_managed(keep=xml_jobs)
            logger.info("Number of jobs deleted: %d", n)
