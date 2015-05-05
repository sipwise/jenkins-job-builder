#!/usr/bin/env python
# Copyright (C) 2015 OpenStack Foundation
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
import os

from six.moves import configparser, StringIO

from jenkins_jobs.errors import JenkinsJobsException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

DEFAULT_CONF = """
[job_builder]
keep_descriptions=False
ignore_cache=False
recursive=False
exclude=.*
allow_duplicates=False
allow_empty_variables=False

[jenkins]
url=http://localhost:8080/
user=
password=
query_plugins_info=True

[hipchat]
authtoken=dummy
send-as=Jenkins
"""


def load(options):

    conf = '/etc/jenkins_jobs/jenkins_jobs.ini'
    if options.conf:
        conf = options.conf
    else:
        # Fallback to script directory
        localconf = os.path.join(os.path.dirname(__file__),
                                 'jenkins_jobs.ini')
        if os.path.isfile(localconf):
            conf = localconf
    config = configparser.ConfigParser()
    # Load default config always
    config.readfp(StringIO(DEFAULT_CONF))
    if os.path.isfile(conf):
        logger.debug("Reading config from {0}".format(conf))
        conffp = open(conf, 'r')
        config.readfp(conffp)
    elif options.command == 'test':
        logger.debug("Not requiring config for test output generation")
    else:
        raise JenkinsJobsException(
            "A valid configuration file is required when not run as a test"
            "\n{0} is not a valid .ini file".format(conf))

    return config
