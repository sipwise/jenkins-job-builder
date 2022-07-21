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

import itertools

from .errors import JenkinsJobsException


def merge_dicts(dict_list):
    result = {}
    for d in dict_list:
        result.update(d)
    return result


class DimensionsExpander:
    def __init__(self, context):
        self._context = context

    def enum_dimensions_params(self, axes, params, defaults):
        if not axes:
            # No axes - instantiate one job/view.
            yield {}
            return
        dim_values = []
        for axis in axes:
            try:
                value = params[axis]
            except KeyError:
                try:
                    value = defaults[axis]
                except KeyError:
                    continue  # May be, value would be received from an another axis values.
            value = self._decode_axis_value(axis, value)
            dim_values.append(value)
        for values in itertools.product(*dim_values):
            yield merge_dicts(values)

    def _decode_axis_value(self, axis, value):
        if not isinstance(value, list):
            yield {axis: value}
            return
        for item in value:
            if not isinstance(item, dict):
                yield {axis: item}
                continue
            if len(item.items()) != 1:
                raise JenkinsJobsException(
                    f"Invalid parameter {axis!r} definition for template {self._context!r}:"
                    f" Expected a value or a dict with single element, but got: {item!r}"
                )
            value, p = next(iter(item.items()))
            yield {
                axis: value,  # Point axis value.
                **p,  # Point-specific parameters. May override asis value.
            }

    def is_point_included(self, exclude_list, params):
        return not any(self._match_exclude(params, el) for el in exclude_list or [])

    def _match_exclude(self, params, exclude):
        if not isinstance(exclude, dict):
            raise JenkinsJobsException(
                f"Template {self._context!r}: Exclude element should be dict, but is: {exclude!r}"
            )
        if not exclude:
            raise JenkinsJobsException(
                f"Template {self._context!r}: Exclude element should be dict, but is empty: {exclude!r}"
            )
        for axis, value in exclude.items():
            try:
                v = params[axis]
            except KeyError:
                raise JenkinsJobsException(
                    f"Template {self._context!r}: Unknown axis {axis!r} for exclude element: {exclude!r}"
                )
            if value != v:
                return False
        # All required exclude values are matched.
        return True
