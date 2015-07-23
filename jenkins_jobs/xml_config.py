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

# Manage Jenkins XML config file output.

import errno
import hashlib
import io
import logging
import os
from xml.dom import minidom
import xml.etree.ElementTree as XML

from jenkins_jobs import utils


logger = logging.getLogger(__name__)


def remove_ignorable_whitespace(node):
    """Remove insignificant whitespace from XML nodes

    It should only remove whitespace in between elements and sub elements.
    This should be safe for Jenkins due to how it's XML serialization works
    but may not be valid for other XML documents. So use this method with
    caution outside of this specific library.
    """
    # strip tail whitespace if it's not significant
    if node.tail and node.tail.strip() == "":
        node.tail = None

    for child in node:
        # only strip whitespace from the text node if there are subelement
        # nodes as this means we are removing leading whitespace before such
        # sub elements. Otherwise risk removing whitespace from an element
        # that only contains whitespace
        if node.text and node.text.strip() == "":
            node.text = None
        remove_ignorable_whitespace(child)


class JenkinsXmlConfig(object):
    def __init__(self, xml, name):
        self.xml = xml
        self.name = name

    def md5(self):
        return hashlib.md5(self.output()).hexdigest()

    def output(self):
        out = minidom.parseString(XML.tostring(self.xml, encoding='UTF-8'))
        return out.toprettyxml(indent='  ', encoding='utf-8')

    def write_xml(self, output):
        if hasattr(output, 'write'):
            # `output` is a file-like object
            logger.info("%s name:  %s", self.kind, self.name)
            logger.debug("Writing XML to '{0}'".format(output))
            output = utils.wrap_stream(output)
            try:
                output.write(self.output())
            except IOError as exc:
                if exc.errno == errno.EPIPE:
                    # EPIPE could happen if piping output to something
                    # that doesn't read the whole input (e.g.: the UNIX
                    # `head` command)
                    return True
                raise
            return False

        output_fn = os.path.join(output, self.name)
        logger.debug("Writing XML to '{0}'".format(output_fn))
        with io.open(output_fn, 'w', encoding='utf-8') as f:
            f.write(self.output().decode('utf-8'))
        return False


class XmlJob(JenkinsXmlConfig):
    kind = 'Job'


class XmlView(JenkinsXmlConfig):
    kind = 'View'
