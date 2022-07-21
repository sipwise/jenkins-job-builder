from dataclasses import dataclass

from .root_base import RootBase, NonTemplateRootMixin, TemplateRootMixin, Group
from .defaults import split_contents_params, view_contents_keys


@dataclass
class ViewBase(RootBase):
    view_type: str

    @classmethod
    def from_dict(cls, config, roots, expander, data):
        keep_descriptions = config.yamlparser["keep_descriptions"]
        d = {**data}
        name = d.pop("name")
        id = d.pop("id", name)
        description = d.pop("description", None)
        defaults = d.pop("defaults", "global")
        view_type = d.pop("view-type", "list")
        contents, params = split_contents_params(d, view_contents_keys)
        return cls(
            roots.defaults,
            expander,
            keep_descriptions,
            id,
            name,
            description,
            defaults,
            params,
            contents,
            view_type,
        )

    def _as_dict(self):
        return {
            "name": self.name,
            "view-type": self.view_type,
            **self.contents,
        }


class View(ViewBase, NonTemplateRootMixin):
    @classmethod
    def add(cls, config, roots, expander, param_expander, data):
        view = cls.from_dict(config, roots, expander, data)
        roots.assign(roots.views, view.id, view, "view")


class ViewTemplate(ViewBase, TemplateRootMixin):
    @classmethod
    def add(cls, config, roots, expander, params_expander, data):
        template = cls.from_dict(config, roots, params_expander, data)
        roots.assign(roots.view_templates, template.id, template, "view template")


@dataclass
class ViewGroup(Group):
    _views: dict
    _view_templates: dict

    @classmethod
    def add(cls, config, roots, expander, params_expander, data):
        d = {**data}
        name = d.pop("name")
        view_specs = [
            cls._spec_from_dict(item, error_context=f"View group {name}")
            for item in d.pop("views")
        ]
        group = cls(
            name,
            view_specs,
            d,
            roots.views,
            roots.view_templates,
        )
        roots.assign(roots.view_groups, group.name, group, "view group")

    def __str__(self):
        return f"View group {self.name}"

    @property
    def _root_dicts(self):
        return [self._views, self._view_templates]
