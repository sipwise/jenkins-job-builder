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

import jenkins_jobs.version

from stevedore import extension


def __version__():
    return "Jenkins Job Builder version: %s" % \
        jenkins_jobs.version.version_info.version_string()


def create_parser():
    """ Create an ArgumentParser object usable by JenkinsJobs. The method
    name is preceded with an underscore even though it is used by JJBConfig
    to signify to API users that it is not guaranteed to exist or exhibit
    the same behavior within the lifetime of the 2.x series of JJB.
    """
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
