# Joint copyright:
#  - Copyright 2012,2013 Wikimedia Foundation
#  - Copyright 2012,2013 Antoine "hashar" Musso
#  - Copyright 2013 Arnaud Fabre
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

import os
from pathlib import Path

import pytest


exceptions_dir = Path(__file__).parent / "job_exceptions"


# Override to avoid scenarios usage.
@pytest.fixture
def config_path():
    return os.devnull


# Override to avoid scenarios usage.
@pytest.fixture
def plugins_info():
    return None


def test_incorrect_template_dimensions(caplog, check_parser):
    in_path = exceptions_dir / "incorrect_template_dimensions.yaml"
    with pytest.raises(Exception) as excinfo:
        check_parser(in_path)
    assert "'NoneType' object is not iterable" in str(excinfo.value)
    assert "- branch: current\n  current: null" in caplog.text


@pytest.mark.parametrize("name", ["template", "params"])
def test_failure_formatting(caplog, check_parser, name):
    in_path = exceptions_dir / f"failure_formatting_{name}.yaml"
    with pytest.raises(Exception):
        check_parser(in_path)
    assert f"Failure formatting {name}" in caplog.text
    assert "Problem formatting with args" in caplog.text
