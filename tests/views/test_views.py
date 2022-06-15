# Copyright 2015 Openstack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.import os

from operator import attrgetter
from pathlib import Path

import pytest

from jenkins_jobs.modules import view_all
from jenkins_jobs.modules import view_delivery_pipeline
from jenkins_jobs.modules import view_list
from jenkins_jobs.modules import view_nested
from jenkins_jobs.modules import view_pipeline
from jenkins_jobs.modules import view_sectioned
from tests.enum_scenarios import scenario_list


fixtures_dir = Path(__file__).parent / "fixtures"


@pytest.fixture(
    params=scenario_list(fixtures_dir),
    ids=attrgetter("name"),
)
def scenario(request):
    return request.param


# But actually this is a view.
@pytest.fixture
def project(input, registry):
    type_to_class = {
        "all": view_all.All,
        "delivery_pipeline": view_delivery_pipeline.DeliveryPipeline,
        "list": view_list.List,
        "nested": view_nested.Nested,
        "pipeline": view_pipeline.Pipeline,
        "sectioned": view_sectioned.Sectioned,
    }
    try:
        class_name = input["view-type"]
    except KeyError:
        raise RuntimeError("'view-type' element is expected in input yaml")
    cls = type_to_class[class_name]
    return cls(registry)


view_class_list = [
    view_all.All,
    view_delivery_pipeline.DeliveryPipeline,
    view_list.List,
    view_nested.Nested,
    view_pipeline.Pipeline,
    view_sectioned.Sectioned,
]


@pytest.mark.parametrize(
    "view_class", [pytest.param(cls, id=cls.__name__) for cls in view_class_list]
)
def test_view(view_class, check_generator):
    check_generator(view_class)
