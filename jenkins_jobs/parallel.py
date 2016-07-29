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

# Parallel execution helper functions and classes

from concurrent import futures
import logging
from multiprocessing import cpu_count
import traceback

import six

logger = logging.getLogger(__name__)


def parallelize(func):
    @six.wraps(func)
    def parallelized(*args, **kwargs):
        """
        This function will spawn workers and run the decorated function in
        parallel on the workers. It will not ensure the thread safety of the
        decorated function (the decorated function should be thread safe by
        itself). It accepts two special parameters:

        :arg list parallelize: list of the arguments to pass to each of the
        runs, the results of each run will be returned in the same order.
        :arg int n_workers: number of workers to use, by default and if '0'
        passed will autodetect the number of cores and use that, if '1'
        passed, it will not use any workers and just run as if were not
        parallelized everything.

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

        This will run the function `parallelized_function` 3 times, in
        parallel (depending on the number of detected cores) and return an
        array with the results of the executions in the same order the
        parameters were passed.
        """
        n_workers = kwargs.pop('n_workers', 0)
        p_kwargs = kwargs.pop('parallelize', [])
        # if only one parameter is passed inside the parallelize dict, run the
        # original function as is, no need for pools
        if len(p_kwargs) == 1:
            kwargs.update(p_kwargs[0])
        if len(p_kwargs) in (1, 0):
            return func(*args, **kwargs)

        # prepare the workers
        # If no number of workers passed or passed 0
        if not n_workers:
            n_workers = cpu_count()
        logging.debug("Running (up to) parallel %d workers", n_workers)

        futs = []
        with futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
            # Feed the workers
            for f_kwargs in p_kwargs:
                f_kwargs.update(kwargs)
                futs.append(executor.submit(func, *args, **f_kwargs))
            # Wait for the results
            logging.debug("Waiting for workers to finish processing")
            futures.wait(futs)

        results = []
        for fut in futs:
            try:
                res = fut.result()
            except Exception as exc:
                # This is somewhat not right (as we just lost telling
                # the caller their thing failed, oh well I guess)...
                res = exc
                traceback.print_exc()
            results.append(res)
        logging.debug("Parallel task finished")
        return results
    return parallelized
