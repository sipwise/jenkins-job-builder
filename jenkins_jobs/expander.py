from functools import partial

from jinja2 import StrictUndefined

from .errors import JenkinsJobsException
from .formatter import CustomFormatter, enum_str_format_required_params
from .yaml_objects import (
    J2String,
    J2Yaml,
    YamlInclude,
    YamlListJoin,
    IncludeJinja2,
    IncludeRaw,
    IncludeRawEscape,
)


def expand_dict(expander, obj, params):
    result = {}
    for key, value in obj.items():
        expanded_key = expander.expand(key, params)
        expanded_value = expander.expand(value, params)
        result[expanded_key] = expanded_value
    return result


def expand_list(expander, obj, params):
    return [expander.expand(item, params) for item in obj]


def expand_tuple(expander, obj, params):
    return tuple(expander.expand(item, params) for item in obj)


class StrExpander:
    def __init__(self, config):
        allow_empty = config.yamlparser["allow_empty_variables"]
        self._formatter = CustomFormatter(allow_empty)

    def __call__(self, obj, params):
        return self._formatter.format(obj, **params)


def call_expand(expander, obj, params):
    return obj.expand(expander, params)


def call_subst(expander, obj, params):
    return obj.subst(expander, params)


def dont_expand(obj, params):
    return obj


yaml_classes_list = [
    J2String,
    J2Yaml,
    YamlInclude,
    YamlListJoin,
    IncludeJinja2,
    IncludeRaw,
    IncludeRawEscape,
]

deprecated_yaml_tags = [
    ("!include", YamlInclude),
    ("!include-raw", IncludeRaw),
    ("!include-raw-escape", IncludeRawEscape),
]


# Does not expand string formats. Used in jobs and macros without parameters.
class Expander:
    def __init__(self, config):
        _yaml_object_expanders = {
            cls: partial(call_expand, self) for cls in yaml_classes_list
        }
        self.expanders = {
            dict: partial(expand_dict, self),
            list: partial(expand_list, self),
            tuple: partial(expand_tuple, self),
            str: dont_expand,
            bool: dont_expand,
            int: dont_expand,
            float: dont_expand,
            type(None): dont_expand,
            **_yaml_object_expanders,
        }

    def expand(self, obj, params):
        t = type(obj)
        try:
            expander = self.expanders[t]
        except KeyError:
            raise RuntimeError(f"Do not know how to expand type: {t!r}")
        return expander(obj, params)


# Expands string formats also. Used in jobs templates and macros with parameters.
class ParamsExpander(Expander):
    def __init__(self, config):
        super().__init__(config)
        _yaml_object_expanders = {
            cls: partial(call_subst, self) for cls in yaml_classes_list
        }
        self.expanders.update(
            {
                str: StrExpander(config),
                **_yaml_object_expanders,
            }
        )


def call_required_params(obj):
    yield from obj.required_params


def enum_dict_params(obj):
    for key, value in obj.items():
        yield from enum_required_params(key)
        yield from enum_required_params(value)


def enum_seq_params(obj):
    for value in obj:
        yield from enum_required_params(value)


def no_parameters(obj):
    return []


yaml_classes_enumers = {cls: call_required_params for cls in yaml_classes_list}

param_enumers = {
    str: enum_str_format_required_params,
    dict: enum_dict_params,
    list: enum_seq_params,
    tuple: enum_seq_params,
    bool: no_parameters,
    int: no_parameters,
    float: no_parameters,
    type(None): no_parameters,
    **yaml_classes_enumers,
}

# Do not expand these.
disable_expand_for = {"template-name"}


def enum_required_params(obj):
    t = type(obj)
    try:
        enumer = param_enumers[t]
    except KeyError:
        raise RuntimeError(
            f"Do not know how to enumerate required parameters for type: {t!r}"
        )
    return enumer(obj)


def expand_parameters(expander, param_dict, template_name):
    expanded_params = {}
    deps = {}  # Using dict as ordered set.

    def expand(name):
        try:
            return expanded_params[name]
        except KeyError:
            pass
        try:
            format = param_dict[name]
        except KeyError:
            return StrictUndefined(name=name)
        if name in deps:
            raise RuntimeError(
                f"While expanding {name!r} for template {template_name!r}:"
                f"  Recursive parameters usage: {name} <- {' <- '.join(deps)}"
            )
        if name in disable_expand_for:
            value = format
        else:
            required_params = list(enum_required_params(format))
            deps[name] = None
            try:
                params = {n: expand(n) for n in required_params}
            finally:
                deps.popitem()
            try:
                value = expander.expand(format, params)
            except JenkinsJobsException as x:
                used_by_deps = ", used by".join(f"{d!r}" for d in deps)
                raise RuntimeError(
                    f"While expanding {name!r}, used by {used_by_deps}, used by template {template_name!r}: {x}"
                )
        expanded_params[name] = value
        return value

    for name in param_dict:
        expand(name)
    return expanded_params
