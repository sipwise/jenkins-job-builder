from unittest.mock import Mock

import pytest

from jenkins_jobs.config import JJBConfig
from jenkins_jobs.yaml_objects import J2String


cases = [
    ("{{ abc }}", {"abc"}),
    ("{% if cond %} {{ x }} {% else %} {{ y }} {% endif %}", {"cond", "x", "y"}),
    ("{# {{ abc }} #}", {}),
]


@pytest.mark.parametrize("format,expected_used_params", cases)
def test_jinja2_required_params(format, expected_used_params):
    config = JJBConfig()
    loader = Mock(source_dir=None)
    template = J2String(config, loader, pos=None, template_text=format)
    assert template.required_params == set(expected_used_params)
