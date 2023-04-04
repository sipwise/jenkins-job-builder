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

from pathlib import Path

from jenkins_jobs.loc_loader import LocLoader

fixtures_dir = Path(__file__).parent / "loc_fixtures"


def test_location():
    print()
    path = fixtures_dir / "sample_01.yaml"
    loader = LocLoader(path.read_text(), str(path))
    data = loader.get_single_data()

    b = data[0]["job_template"]["builders"][0]
    print(type(b), b.pos)
    print(b)
    print(b.pos.snippet)

    b = data[0]["job_template"]["builders"][1]["sample_macro"]
    print(type(b), b.pos)
    print(b)
    print("items", b.value_pos)
    for key, pos in b.value_pos.items():
        print("item:", key, pos)
        print(pos.snippet)

    b = data[0]["job_template"]["builders"]
    print(type(b), b.pos)
    print(b)
    print("items", b.value_pos)
    for idx, pos in enumerate(b.value_pos):
        print("item:", idx, pos)

    print("--- sample-job-2 builders -------------------------------------------")
    b = data[1]["job_template"]["builders"]
    print(type(b), b.pos)
    print(b)
    print("items", b.value_pos)
    for idx, pos in enumerate(b.value_pos):
        print("item:", idx, pos)
        print(pos.snippet)

    print("--- sample-job-2 sample_macro ---------------------------------------")
    sample_macro = data[1]["job_template"]["builders"][1]["sample_macro"]
    param_2_pos = sample_macro.value_pos["param_2"]
    print(param_2_pos)
    print(param_2_pos.snippet)
    assert param_2_pos.line == 9
    assert param_2_pos.column == 19
    assert param_2_pos.snippet.splitlines()[0].strip() == "param_2: value_2"

    print("--- third template -------------------------------------------------")
    b = data[2]["job_template"]["builders"][0]["sample_macro"]
    print(type(b), b.pos)
    print(b)
    print("items", b.value_pos)
    for key, pos in b.key_pos.items():
        print("keys for item:", key, pos)
    for key, pos in b.value_pos.items():
        print("values for item:", key, pos)
