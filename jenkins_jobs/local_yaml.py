#!/usr/bin/env python
# Copyright (C) 2013 Hewlett-Packard.
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

# Provide local yaml parsing classes and extend yaml module

import functools
import logging
import re
import os
import yaml

logger = logging.getLogger(__name__)


class LocalLoader(yaml.Loader):
    """Subclass for yaml.Loader which handles the local tags 'include' and
    include-raw to specify a file to include yaml code from. This is done in
    yaml files by "!include path/to/file.yaml". When constructed, should pass
    a search path list to look under for the file, taking the first match
    found. Code will in addition look under the same directory containing the
    yaml file or the current working directory.

    The tag '!include' will in turn be parsed by yaml, so further yaml
    configuration and contents may be passed, while the tag '!include-raw'
    is used to inline blobs of data. A final tag '!include-raw-escape' is used
    to deal with the special case of how substitution is performed on job
    templates.

    The tag '!include-raw' will treat the file as a block of data, to be
    read into the calling yaml construct without any further parsing. Any
    yaml code in a file included through this tag, will be treated as string
    data.

    The tag '!include-raw-escape' treats the given file as a block of data
    by calling the same function as '!include-raw' uses, and subsequently
    applies a callback function to allow the caller to escape any special
    characters that may cause problems in subsequent processing. This allows
    job-templates to use this tag to include scripts from files without
    needing to escape braces in the original file.

    Can include arbitrary files as a method of having blocks of data managed
    separately to the yaml job configurations. Inlining scripts contained in
    separate files is one specific use case, althought this method may also
    be used instead of macros in certain cases.

    Examples::

        job:
          name: test-job-1
          wrappers:
            !include my/defaults/wrappers.yaml

        job:
          name: test-job-2
          builders:
            - shell:
              !include-raw path/to/script1
            - shell:
              !include-raw path/to/script2

        job-template:
          name: test-template-1-{my_var}
          builders:
            - shell:
              !include-raw-escaped path/to/script1
            - builders-from: {custom_build_job_1}


    Loading::
        # use the load function provided in this file
        import local_yaml
        data = local_yaml.load(open(fn))


        # Loading by providing the alternate class to the default yaml load
        from local_yaml import LocalLoader
        data = yaml.load(open(fn), LocalLoader)

        # Loading with a search path
        from local_yaml import LocalLoader
        import functools
        data = yaml.load(open(fn),
                         functools.partial(LocalLoader,
                                           search_path=['path'])
                        )
    """

    def __init__(self, *args, **kwargs):
        # make sure to pop off any local settings before passing to
        # the parent constructor as any unknown args may cause errors.
        self.search_path = set()
        if 'search_path' in kwargs:
            for p in kwargs.pop('search_path'):
                self.search_path.add(os.path.normpath(p))

        if 'escape_callback' in kwargs:
            self._escape = kwargs.pop('escape_callback')

        super(LocalLoader, self).__init__(*args, **kwargs)

        # Add tag constructors
        self.add_constructor('!include', self._include_tag)
        self.add_constructor('!include-raw', self._include_raw_tag)
        self.add_constructor('!include-raw-escape',
                             self._include_raw_escape_tag)

        if isinstance(self.stream, file):
            self.search_path.add(os.path.normpath(
                os.path.dirname(self.stream.name)))
        self.search_path.add(os.path.normpath(os.path.curdir))

    def _find_file(self, filename):
        for dirname in self.search_path:
            candidate = os.path.expanduser(os.path.join(dirname, filename))
            if os.path.isfile(candidate):
                logger.info("Including file '{0}' from path '{0}'"
                            .format(filename, dirname))
                return candidate
        return filename

    def _include_tag(self, loader, node):
        filename = self._find_file(loader.construct_yaml_str(node))
        with open(filename, 'r') as f:
            data = yaml.load(f, functools.partial(LocalLoader,
                                                  search_path=self.search_path
                                                  ))
        return data

    def _include_raw_tag(self, loader, node):
        filename = self._find_file(loader.construct_yaml_str(node))
        with open(filename, 'r') as f:
            data = f.read()
        return data

    def _include_raw_escape_tag(self, loader, node):
        return self._escape(self._include_raw_tag(loader, node))

    def _escape(self, data):
        return re.sub(r'({|})', r'\1\1', data)


def load(stream, **kwargs):
    return yaml.load(stream, functools.partial(LocalLoader, **kwargs))
