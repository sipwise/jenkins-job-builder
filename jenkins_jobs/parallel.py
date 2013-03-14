#!/usr/bin/env python
# Copyright (C) 2013,2014,2015 Hewlett-Packard Development Company, L.P.
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

# Manage jobs in Jenkins server

from functools import wraps
import logging
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
import sys
import traceback


logger = logging.getLogger(__name__)


def _run_task(func, data={}, *args, **kwargs):
    kwargs.update(data)
    try:
        result = func(*args, **kwargs)
    except Exception as exc:
        result = exc
        logger.error("Exception occurred running: %s(%s, %s)" %
                     (func.__name__, ", ".join(str(val) for val in args),
                      ", ".join("%s=%s" % (k, v) for k, v in kwargs.items())))
        logger.debug(traceback.print_exc())

    return result


def parallelize(func):
    @wraps(func)
    def parallel_exec(*args, **kwargs):
        """
        This decorator will run the decorated function in parallel using the
        multiprocessing map_async function. It will not ensure the thread
        safety of the decorated function. It accepts some special parameters.

        :arg list parallelize: list of the arguments to pass to each of the
          runs, the results of each run will be returned in the same order.
        :arg int n_workers: number of workers to use, by default and if '0'
          passed will autodetect the number of cores and use that, if '1'
          passed, it will be single threaded.

        Example:

        > @parallelize
        > def sample(param1, param2, param3):
        >     return param1 + param2 + param3
        >
        > sample('param1', param2='val2',
        >        parallelize=[
        >            {'param3': 'val3'},
        >            {'param3': 'val4'},
        >            {'param3': 'val5'},
        >        ])
        >
        ['param1val2val3', 'param1val2val4', 'param1val2val5']

        This will run the `sample` function 3 times, in parallel (depending
        on the number of detected cores) and return an array with the results
        of the executions in the same order the parameters were passed.
        """

        data = kwargs.pop('parallelize')

        # multiprocessing threading call map_async hangs with iterables of
        # length 0. see http://bugs.python.org/issue12157
        if len(data) == 0:
            return

        n_workers = kwargs.pop('n_workers', 0)
        if not n_workers:
            n_workers = cpu_count()
        pool = ThreadPool(processes=min(n_workers, len(data)))

        # Use lambda to control the position of the parallel data to be passed
        # as the first arg to the run_task function as functools.partial can
        # only append such args.
        result = pool.map_async(
            lambda datum: _run_task(func, datum, *args, **kwargs), data,
            chunksize=1)

        pool.close()
        try:
            while True:
                if result.ready():
                    break
                result.wait(.2)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, terminating all threads")
            pool.terminate()
            raise
        finally:
            pool.join()
            logger.debug("All running threads are finished")

        results = []
        try:
            results = result.get()
        except:
            print("Unexpected error:", sys.exc_info()[0])
            print("Error value:", sys.exc_info()[1])
            print("Traceback:", sys.exc_info()[2])
        else:
            if not result.successful():
                for i, r in enumerate(results):
                    if not r:
                        logger.error("Problem processing datum '%s'" % data[i])

        return results

    return parallel_exec
