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

import argparse
import logging
import sys

import jenkins_jobs.version
from jenkins_jobs import cmd

from stevedore import extension

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def __version__():
    return "Jenkins Job Builder version: %s" % \
        jenkins_jobs.version.version_info.version_string()


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
        parser = self._create_parser()
        self._options = parser.parse_args(args)

        if not self._options.command:
            parser.error("Must specify a 'command' to be performed")

        if (self._options.log_level is not None):
            self._options.log_level = getattr(logging,
                                              self._options.log_level.upper(),
                                              logger.getEffectiveLevel())
            logger.setLevel(self._options.log_level)

        self.__config_file_values = cmd.setup_config_settings(self._options)

    def _create_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--conf', dest='conf', help='configuration file')
        parser.add_argument('-l',
                            '--log_level',
                            dest='log_level',
                            default='info',
                            help="log level (default: %(default)s)")
        parser.add_argument(
            '--ignore-cache',
            action='store_true',
            dest='ignore_cache',
            default=False,
            help='ignore the cache and update the jobs anyhow (that will only '
            'flush the specified jobs cache)')
        parser.add_argument(
            '--flush-cache',
            action='store_true',
            dest='flush_cache',
            default=False,
            help='flush all the cache entries before updating')
        parser.add_argument('--version',
                            dest='version',
                            action='version',
                            version=__version__(),
                            help='show version')
        parser.add_argument(
            '--allow-empty-variables',
            action='store_true',
            dest='allow_empty_variables',
            default=None,
            help='''Don\'t fail if any of the variables inside any string are
            not defined, replace with empty string instead.
            ''')

        subparser = parser.add_subparsers(help='update, test or delete job',
                                          dest='command')

        extension_manager = extension.ExtensionManager(
            namespace='jjb.cli.subcommands',
            invoke_on_load=True,
        )

        def parse_subcommand_args(ext, subparser):
            ext.obj.parse_args(subparser)

        extension_manager.map(parse_subcommand_args, subparser)

        return parser

    def execute(self):
        jenkins_jobs.cmd.execute(self._options, self.__config_file_values)


def main():
    argv = sys.argv[1:]
    jjb = JenkinsJobs(argv)
    jjb.execute()
