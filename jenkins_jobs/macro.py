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

from dataclasses import dataclass
from functools import partial

from .errors import JenkinsJobsException
from .position import Pos


macro_specs = [
    # type_name, elements_name (aka component_type, component_list_type for Registry).
    ("parameter", "parameters"),
    ("property", "properties"),
    ("builder", "builders"),
    ("wrapper", "wrappers"),
    ("trigger", "triggers"),
    ("publisher", "publishers"),
    ("scm", "scm"),
    ("pipeline-scm", "pipeline-scm"),
    ("reporter", "reporters"),
]


@dataclass
class Macro:
    name: str
    pos: Pos
    elements: list

    @classmethod
    def add(
        cls,
        type_name,
        elements_name,
        config,
        roots,
        expander,
        params_expander,
        data,
        pos,
    ):
        d = data.copy()
        name = d.pop_required_loc_string("name")
        elements = d.pop_required_element(elements_name)
        if d:
            example_key = next(iter(d.keys()))
            raise JenkinsJobsException(
                f"In {type_name} macro {name!r}: unexpected elements: {','.join(d.keys())}",
                pos=data.key_pos.get(example_key),
            )
        macro = cls(name, pos, elements or [])
        roots.assign(roots.macros[type_name], name, macro, "macro")


macro_adders = {
    macro_type: partial(Macro.add, macro_type, elements_name)
    for macro_type, elements_name in macro_specs
}
