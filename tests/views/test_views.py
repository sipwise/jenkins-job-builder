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

import os
from jenkins_jobs.modules import view_all
from jenkins_jobs.modules import view_delivery_pipeline
from jenkins_jobs.modules import view_list
from jenkins_jobs.modules import view_nested
from jenkins_jobs.modules import view_pipeline
from jenkins_jobs.modules import view_sectioned
from tests import base


class TestCaseModuleViewAll(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
    scenarios = base.get_scenarios(fixtures_path)
    klass = view_all.All


class TestCaseModuleViewDeliveryPipeline(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
    scenarios = base.get_scenarios(fixtures_path)
    klass = view_delivery_pipeline.DeliveryPipeline


class TestCaseModuleViewList(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
    scenarios = base.get_scenarios(fixtures_path)
    klass = view_list.List


class TestCaseModuleViewNested(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
    scenarios = base.get_scenarios(fixtures_path)
    klass = view_nested.Nested


class TestCaseModuleViewPipeline(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
    scenarios = base.get_scenarios(fixtures_path)
    klass = view_pipeline.Pipeline


class TestCaseModuleViewSectioned(base.BaseScenariosTestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures")
    scenarios = base.get_scenarios(fixtures_path)
    klass = view_sectioned.Sectioned
