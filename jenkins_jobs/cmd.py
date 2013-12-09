#!/usr/bin/env python
# Copyright (C) 2012 OpenStack Foundation
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
import ConfigParser
import logging
import os
import sys


def confirm(question):
    answer = raw_input('%s (Y/N): ' % question).upper().strip()
    if not answer == 'Y':
        sys.exit('Aborted')


def main():
    import jenkins_jobs.builder
    import jenkins_jobs.errors
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(help='list, update, test or delete job',
                                      dest='command')
    parser_list = subparser.add_parser('list')
    list_remote = parser_list.add_mutually_exclusive_group(required=True)
    list_remote.add_argument('--local', help='List jobs defined in --path',
                             action='store_true')
    list_remote.add_argument('--remote', help='List Jenkins target jobs',
                             action='store_true')
    parser_update = subparser.add_parser('update')
    parser_update.add_argument('names', help='name(s) of job(s)', nargs='*')
    parser_update.add_argument('--delete-old', help='Delete obsolete jobs',
                               action='store_true',
                               dest='delete_old', default=False,)
    parser_test = subparser.add_parser('test')
    parser_test.add_argument('-o', dest='output_dir', required=True,
                             help='Path to output XML')
    parser_test.add_argument('name', help='name(s) of job(s)', nargs='*')
    parser_delete = subparser.add_parser('delete')
    parser_delete.add_argument('name', help='name of job', nargs='+')
    subparser.add_parser('delete-all',
                         help='Delete *ALL* jobs from Jenkins server, '
                         'including those not managed by Jenkins Job '
                         'Builder.')
    parser.add_argument('--conf', dest='conf', help='Configuration file')
    parser.add_argument('-l', '--log_level', dest='log_level', default='info',
                        help="Log level (default: %(default)s)")
    parser.add_argument('-p', '--path', help='Path to YAML file or directory')
    parser.add_argument(
        '--ignore-cache', action='store_true',
        dest='ignore_cache', default=False,
        help='Ignore the cache and update the jobs anyhow (that will only '
             'flush the specified jobs cache)')
    parser.add_argument(
        '--flush-cache', action='store_true', dest='flush_cache',
        default=False, help='Flush all the cache entries before updating')
    options = parser.parse_args()

    options.log_level = getattr(logging, options.log_level.upper(),
                                logging.INFO)
    logging.basicConfig(level=options.log_level)
    logger = logging.getLogger()

    conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    if options.conf:
        conf = options.conf
    else:
        # Fallback to script directory
        localconf = os.path.join(os.path.dirname(__file__),
                                 'jenkins_jobs.ini')
        if os.path.isfile(localconf):
            conf = localconf

    config = ConfigParser.ConfigParser()
    if os.path.isfile(conf):
        logger.debug("Reading config from {0}".format(conf))
        conffp = open(conf, 'r')
        config.readfp(conffp)
    elif (options.command == 'test'
          or (options.command == 'list' and options.local)
          ):
        ## to avoid the 'no section' and 'no option' errors when testing
        config.add_section("jenkins")
        config.set("jenkins", "url", "http://localhost:8080")
        config.set("jenkins", "user", None)
        config.set("jenkins", "password", None)
        logger.debug("Not reading config for local listing or test output "
                     "generation")
    else:
        raise jenkins_jobs.errors.JenkinsJobsException(
            "A valid configuration file is required when not run as a test "
            "or local list")

    logger.debug("Config: {0}".format(config))
    builder = jenkins_jobs.builder.Builder(config.get('jenkins', 'url'),
                                           config.get('jenkins', 'user'),
                                           config.get('jenkins', 'password'),
                                           config,
                                           ignore_cache=options.ignore_cache,
                                           flush_cache=options.flush_cache)

    if (options.command in ['delete', 'list', 'test', 'update']
            and options.path is None
            and options.remote is not True):

        logger.error('Command %s require YAML configuration files.',
                     options.command)
        logger.error('Use --path to specifiy a directory/file')
        sys.exit(1)

    if options.command == 'delete':
        for job in options.name:
            logger.info("Deleting jobs in [{0}]".format(job))
            builder.delete_job(job, options.path)
    elif options.command == 'delete-all':
        confirm('Sure you want to delete *ALL* jobs from Jenkins server?\n'
                '(including those not managed by Jenkins Job Builder)')
        logger.info("Deleting all jobs")
        builder.delete_all_jobs()
    elif options.command == 'list':
        jobs = []
        if options.remote:
            logger.info("Listing jobs on remote Jenkins")
            jobs = builder.list_remote_jobs()
        elif options.path:
            logger.info("Listing jobs generated by local config")
            jobs = builder.list_local_jobs(options.path)
        for job_name in jobs:
            print job_name
        logger.info("Found %s jobs on remote Jenkins", len(jobs))

    elif options.command == 'update':
        logger.info("Updating jobs in {0} ({1})".format(
            options.path, options.names))
        jobs = builder.update_job(options.path, options.names)
        if options.delete_old:
            builder.delete_old_managed(keep=[x.name for x in jobs])
    elif options.command == 'test':
        builder.update_job(options.path, options.name,
                           output_dir=options.output_dir)

if __name__ == '__main__':
    sys.path.insert(0, '.')
    main()
