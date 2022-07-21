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

from collections import namedtuple
from dataclasses import dataclass

from .constants import MAGIC_MANAGE_STRING
from .errors import JenkinsJobsException
from .formatter import enum_str_format_required_params, enum_str_format_param_defaults
from .expander import Expander, expand_parameters
from .defaults import Defaults
from .dimensions import DimensionsExpander


@dataclass
class RootBase:
    """Base class for YAML root elements - job, view or template"""

    _defaults: dict
    _expander: Expander
    _keep_descriptions: bool
    _id: str
    name: str
    description: str
    defaults_name: str
    params: dict
    contents: dict

    @property
    def id(self):
        if self._id:
            return self._id
        else:
            return self.name

    def _format_description(self, params):
        if self.description is None:
            defaults = self._pick_defaults(self.defaults_name)
            description = defaults.params.get("description")
        else:
            description = self.description
        if description is None and self._keep_descriptions:
            return {}
        expanded_desc = self._expander.expand(description, params)
        return {"description": (expanded_desc or "") + MAGIC_MANAGE_STRING}

    def _pick_defaults(self, name, merge_global=True):
        try:
            defaults = self._defaults[name]
        except KeyError:
            if name == "global":
                return Defaults.empty()
            raise JenkinsJobsException(
                f"Job template {self.name!r} wants defaults {self.defaults_name!r}"
                " but it was never defined"
            )
        if name == "global":
            return defaults
        if merge_global:
            return defaults.merged_with_global(self._pick_defaults("global"))
        else:
            return defaults


class NonTemplateRootMixin:
    def top_level_generate_items(self):
        defaults = self._pick_defaults(self.defaults_name, merge_global=False)
        description = self._format_description(params={})
        data = self._as_dict()
        contents = self._expander.expand(data, self.params)
        yield {
            **defaults.contents,
            **contents,
            **description,
        }

    def generate_items(self, defaults_name, params):
        # Do not produce jobs/views from under project - they are produced when
        # processed directly from roots, by top_level_generate_items.
        return []


class TemplateRootMixin:
    def generate_items(self, defaults_name, params):
        defaults = self._pick_defaults(defaults_name or self.defaults_name)
        item_params = {
            **defaults.params,
            **self.params,
            **params,
            "template-name": self.name,
        }
        if self._id:
            item_params["id"] = self._id
        contents = {
            **defaults.contents,
            **self._as_dict(),
        }
        axes = list(enum_str_format_required_params(self.name))
        axes_defaults = dict(enum_str_format_param_defaults(self.name))
        dim_expander = DimensionsExpander(context=self.name)
        for dim_params in dim_expander.enum_dimensions_params(
            axes, item_params, axes_defaults
        ):
            instance_params = {
                **item_params,
                **dim_params,
            }
            expanded_params = expand_parameters(
                self._expander, instance_params, template_name=self.name
            )
            exclude_list = expanded_params.get("exclude")
            if not dim_expander.is_point_included(exclude_list, expanded_params):
                continue
            description = self._format_description(expanded_params)
            expanded_contents = self._expander.expand(contents, expanded_params)
            yield {
                **expanded_contents,
                **description,
            }


class GroupBase:
    Spec = namedtuple("Spec", "name params")

    def __repr__(self):
        return f"<{self}>"

    @classmethod
    def _spec_from_dict(cls, d, error_context):
        if isinstance(d, str):
            return cls.Spec(d, params={})
        if not isinstance(d, dict):
            raise JenkinsJobsException(
                f"{error_context}: Job/view spec should name or dict,"
                f" but is {type(d)}. Missing indent?"
            )
        if len(d) != 1:
            raise JenkinsJobsException(
                f"{error_context}: Job/view dict should be single-item,"
                f" but have keys {list(d.keys())}. Missing indent?"
            )
        name, params = next(iter(d.items()))
        if params is None:
            params = {}
        else:
            if not isinstance(params, dict):
                raise JenkinsJobsException(
                    f"{error_context}: Job/view {name} params type should be dict,"
                    f" but is {type(params)} ({params})."
                )
        return cls.Spec(name, params)

    def _generate_items(self, root_dicts, spec_list, defaults_name, params):
        for spec in spec_list:
            item = self._pick_item(root_dicts, spec.name)
            item_params = {
                **params,
                **self.params,
                **self._my_params,
                **spec.params,
            }
            yield from item.generate_items(defaults_name, item_params)

    @property
    def _my_params(self):
        return {}

    def _pick_item(self, root_dict_list, name):
        for roots_dict in root_dict_list:
            try:
                return roots_dict[name]
            except KeyError:
                pass
        raise JenkinsJobsException(
            f"{self}: Failed to find suitable job/view/template named '{name}'"
        )


@dataclass
class Group(GroupBase):
    name: str
    specs: list  # list[Spec]
    params: dict

    def generate_items(self, defaults_name, params):
        return self._generate_items(self._root_dicts, self.specs, defaults_name, params)
