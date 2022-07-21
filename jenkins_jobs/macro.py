from dataclasses import dataclass
from functools import partial

from .errors import JenkinsJobsException


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
    elements: list

    @classmethod
    def add(
        cls, type_name, elements_name, config, roots, expander, params_expander, data
    ):
        d = {**data}
        name = d.pop("name")
        elements = d.pop(elements_name)
        if d:
            raise JenkinsJobsException(
                f"Macro {type_name} {name!r}: unexpected elements: {','.join(d.keys())}"
            )
        macro = cls(name, elements or [])
        roots.assign(roots.macros[type_name], name, macro, "macro")


macro_adders = {
    macro_type: partial(Macro.add, macro_type, elements_name)
    for macro_type, elements_name in macro_specs
}
