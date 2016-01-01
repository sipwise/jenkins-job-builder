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

from jenkins_jobs import utils
from jenkins_jobs.builder import Builder
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.cli.parser import create_parser
from jenkins_jobs.config import JJBConfig
from jenkins_jobs.errors import JenkinsJobsException


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JenkinsJobs(object):
    """ This is the entry point class for the `jenkins-jobs` command line tool.
    While this class can be used programmatically by external users of the JJB
    API, the main goal here is to abstract the `jenkins_jobs` tool in a way
    that prevents test suites from caring overly much about various
    implementation details--for example, tests of subcommands must not have
    access to directly modify configuration objects, instead they must provide
    a fixture in the form of an .ini file that provides the configuration
    necessary for testing.

    External users of the JJB API may be interested in this class as an
    alternative to wrapping `jenkins_jobs` with a subprocess that execs it as a
    system command; instead, python scripts may be written that pass
    `jenkins_jobs` args directly to this class to allow programmatic setting of
    various command line parameters.
    """

    def __init__(self, args=None):
        if args is None:
            args = []
        parser = create_parser()
        options = parser.parse_args(args)

        self.jjb_config = JJBConfig(arguments=options)
        self.jjb_config.do_magical_things()

        if not options.command:
            parser.error("Must specify a 'command' to be performed")

        if (options.log_level is not None):
            options.log_level = getattr(logging,
                                        options.log_level.upper(),
                                        logger.getEffectiveLevel())
            logger.setLevel(options.log_level)

    def execute(self):
        options = self.jjb_config.arguments
        builder = Builder(self.jjb_config)

        if options.command == 'delete':
            for job in options.name:
                builder.delete_job(job, options.path)

        elif options.command == 'delete-all':
            utils.confirm('''Sure you want to delete *ALL* jobs from Jenkins
                          server?\n (including those not managed by Jenkins Job
                          Builder)''')
            logger.info("Deleting all jobs")
            builder.delete_all_jobs()

        elif options.command == 'update':
            if options.n_workers < 0:
                raise JenkinsJobsException(
                    'Number of workers must be equal or greater than 0')

            logger.info("Updating jobs in {0} ({1})".format(
                options.path, options.names))
            orig = time.time()

            # Generate XML
            parser = YamlParser(self.jjb_config, builder.plugins_list)
            parser.load_files(options.path)
            parser.expandYaml(options.names)
            parser.generateXML()

            jobs = parser.jobs
            step = time.time()
            logging.debug('%d XML files generated in %ss',
                          len(jobs), str(step - orig))

            jobs, num_updated_jobs = builder.update_jobs(
                parser.xml_jobs,
                n_workers=options.n_workers)
            logger.info("Number of jobs updated: %d", num_updated_jobs)

            if options.delete_old:
                n = builder.delete_old_managed(keep=parser.xml_jobs)
                logger.info("Number of jobs deleted: %d", n)

        elif options.command == 'test':
            logger.info("Updating jobs in {0} ({1})".format(
                options.path, options.name))
            orig = time.time()

            # Generate XML
            parser = YamlParser(self.jjb_config, builder.plugins_list)
            parser.load_files(options.path)
            parser.expandYaml(options.name)
            parser.generateXML()

            jobs = parser.jobs
            step = time.time()
            logging.debug('%d XML files generated in %ss',
                          len(jobs), str(step - orig))

            builder.update_jobs(parser.xml_jobs, output=options.output_dir,
                                n_workers=1)


def main():
    argv = sys.argv[1:]
    jjb = JenkinsJobs(argv)
    jjb.execute()
