import configparser
import pkg_resources
import xml.etree.ElementTree as XML
from pathlib import Path

import pytest

from jenkins_jobs.alphanum import AlphanumSort
from jenkins_jobs.config import JJBConfig
from jenkins_jobs.modules import project_externaljob
from jenkins_jobs.modules import project_flow
from jenkins_jobs.modules import project_githuborg
from jenkins_jobs.modules import project_matrix
from jenkins_jobs.modules import project_maven
from jenkins_jobs.modules import project_multibranch
from jenkins_jobs.modules import project_multijob
from jenkins_jobs.parser import YamlParser
from jenkins_jobs.registry import ModuleRegistry
from jenkins_jobs.xml_config import XmlJob, XmlJobGenerator, XmlViewGenerator
import jenkins_jobs.local_yaml as yaml


# Avoid writing to ~/.cache/jenkins_jobs.
@pytest.fixture(autouse=True)
def job_cache_mocked(mocker):
    mocker.patch("jenkins_jobs.builder.JobCache", autospec=True)


@pytest.fixture
def config_path(scenario):
    return scenario.config_path


@pytest.fixture
def jjb_config(config_path):
    config = JJBConfig(config_path)
    config.validate()
    return config


@pytest.fixture
def mock_iter_entry_points():
    config = configparser.ConfigParser()
    config.read(Path(__file__).parent / "../setup.cfg")
    groups = {}
    for key in config["entry_points"]:
        groups[key] = list()
        for line in config["entry_points"][key].split("\n"):
            if "" == line.strip():
                continue
            groups[key].append(
                pkg_resources.EntryPoint.parse(line, dist=pkg_resources.Distribution())
            )

    def iter_entry_points(group, name=None):
        return (entry for entry in groups[group] if name is None or name == entry.name)

    return iter_entry_points


@pytest.fixture
def input(scenario):
    return yaml.load(scenario.in_path.read_text())


@pytest.fixture
def plugins_info(scenario):
    if not scenario.plugins_info_path.exists():
        return None
    return yaml.load(scenario.plugins_info_path.read_text())


@pytest.fixture
def registry(mocker, mock_iter_entry_points, jjb_config, plugins_info):
    mocker.patch("pkg_resources.iter_entry_points", side_effect=mock_iter_entry_points)
    return ModuleRegistry(jjb_config, plugins_info)


@pytest.fixture
def project(input, registry):
    type_to_class = {
        "maven": project_maven.Maven,
        "matrix": project_matrix.Matrix,
        "flow": project_flow.Flow,
        "githuborg": project_githuborg.GithubOrganization,
        "multijob": project_multijob.MultiJob,
        "multibranch": project_multibranch.WorkflowMultiBranch,
        "multibranch-defaults": project_multibranch.WorkflowMultiBranchDefaults,
        "externaljob": project_externaljob.ExternalJob,
    }
    try:
        class_name = input["project-type"]
    except KeyError:
        return None
    if class_name == "freestyle":
        return None
    cls = type_to_class[class_name]
    return cls(registry)


@pytest.fixture
def expected_output(scenario):
    if not scenario.out_paths:
        # Do not check output if there are no files for it.
        return None
    return "".join(path.read_text() for path in sorted(scenario.out_paths))


@pytest.fixture
def expected_error(scenario):
    if scenario.error_path.exists():
        return scenario.error_path.read_text().rstrip()
    else:
        return None


def check_folder(scenario, jjb_config, input):
    if "name" not in input:
        return
    parser = YamlParser(jjb_config)
    *dirs, name = parser._getfullname(input).split("/")
    input_dir = scenario.in_path.parent
    expected_out_dirs = [input_dir.joinpath(*dirs)]
    actual_out_dirs = [path.parent for path in scenario.out_paths]
    assert expected_out_dirs == actual_out_dirs


@pytest.fixture
def check_generator(scenario, input, expected_output, jjb_config, registry, project):
    registry.set_parser_data({})

    def check(Generator):
        if project:
            xml = project.root_xml(input)
        else:
            xml = XML.Element("project")

        generator = Generator(registry)
        generator.gen_xml(xml, input)
        check_folder(scenario, jjb_config, input)
        pretty_xml = XmlJob(xml, "fixturejob").output().decode()
        assert expected_output == pretty_xml

    return check


@pytest.fixture
def check_parser(jjb_config, registry):
    parser = YamlParser(jjb_config)

    def check(in_path):
        parser.parse(str(in_path))
        registry.set_parser_data(parser.data)
        job_data_list, job_view_list = parser.expandYaml(registry)
        generator = XmlJobGenerator(registry)
        _ = generator.generateXML(job_data_list)

    return check


@pytest.fixture
def check_job(scenario, expected_output, jjb_config, registry):
    parser = YamlParser(jjb_config)

    def check():
        parser.parse(str(scenario.in_path))
        registry.set_parser_data(parser.data)
        job_data_list, view_data_list = parser.expandYaml(registry)
        generator = XmlJobGenerator(registry)
        job_xml_list = generator.generateXML(job_data_list)
        job_xml_list.sort(key=AlphanumSort)

        pretty_xml = (
            "\n".join(job.output().decode() for job in job_xml_list)
            .strip()
            .replace("\n\n", "\n")
        )
        if expected_output is None:
            return
        stripped_expected_output = (
            expected_output.strip().replace("<BLANKLINE>", "").replace("\n\n", "\n")
        )
        assert stripped_expected_output == pretty_xml

    return check


@pytest.fixture
def check_view(scenario, expected_output, jjb_config, registry):
    parser = YamlParser(jjb_config)

    def check():
        parser.parse(str(scenario.in_path))
        registry.set_parser_data(parser.data)
        job_data_list, view_data_list = parser.expandYaml(registry)
        generator = XmlViewGenerator(registry)
        view_xml_list = generator.generateXML(view_data_list)
        view_xml_list.sort(key=AlphanumSort)

        pretty_xml = (
            "\n".join(view.output().decode() for view in view_xml_list)
            .strip()
            .replace("\n\n", "\n")
        )
        if expected_output is None:
            return
        stripped_expected_output = (
            expected_output.strip().replace("<BLANKLINE>", "").replace("\n\n", "\n")
        )
        assert stripped_expected_output == pretty_xml

    return check
