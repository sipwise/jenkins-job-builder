import configparser
import pkg_resources
import xml.etree.ElementTree as XML
from pathlib import Path

import pytest
import yaml

from jenkins.plugins import Plugin
from jenkins_jobs.alphanum import AlphanumSort
from jenkins_jobs.config import JJBConfig
from jenkins_jobs.loader import Loader
from jenkins_jobs.modules import project_externaljob
from jenkins_jobs.modules import project_flow
from jenkins_jobs.modules import project_githuborg
from jenkins_jobs.modules import project_matrix
from jenkins_jobs.modules import project_maven
from jenkins_jobs.modules import project_multibranch
from jenkins_jobs.modules import project_multijob
from jenkins_jobs.registry import ModuleRegistry
from jenkins_jobs.xml_config import XmlJob, XmlJobGenerator, XmlViewGenerator
from jenkins_jobs import utils

from jenkins_jobs.roots import Roots
from jenkins_jobs.loader import load_files


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
def input(scenario, jjb_config):
    loader = Loader.empty(jjb_config)
    return loader.load_path(scenario.in_path)


@pytest.fixture
def plugins_info(scenario):
    if not scenario.plugins_info_path.exists():
        return None
    plugin_dict_list = yaml.safe_load(scenario.plugins_info_path.read_text())
    return [Plugin(**plugin_dict) for plugin_dict in plugin_dict_list]


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


# Tests use output files directories as expected folder name.
def check_folders(scenario, job_xml_list):
    root_dir = scenario.in_path.parent

    def name_parent(name):
        *dirs, name = name.split("/")
        return "/".join(dirs)

    def path_parent(path):
        if scenario.in_path.is_dir():
            # In directory tests, output file directory does not
            # indicate expected job folder.
            base_dir = scenario.in_path
        else:
            base_dir = root_dir
        dir = str(path.relative_to(base_dir).parent)
        if dir == ".":
            return ""
        else:
            return dir

    actual_dirs = list(sorted(set(name_parent(jx.name) for jx in job_xml_list)))
    expected_dirs = list(sorted(path_parent(path) for path in scenario.out_paths))
    assert expected_dirs == actual_dirs


@pytest.fixture
def check_generator(scenario, input, expected_output, jjb_config, registry, project):
    def check(Generator):
        if project:
            xml = project.root_xml(input)
        else:
            xml = XML.Element("project")

        generator = Generator(registry)
        generator.gen_xml(xml, input)
        pretty_xml = XmlJob(xml, "fixturejob").output().decode()
        assert expected_output == pretty_xml

    return check


@pytest.fixture
def check_parser(jjb_config, registry):
    def check(in_path):
        roots = Roots(jjb_config)
        load_files(jjb_config, roots, [in_path])
        registry.set_macros(roots.macros)
        job_data_list = roots.generate_jobs()
        view_data_list = roots.generate_views()
        generator = XmlJobGenerator(registry)
        _ = generator.generateXML(job_data_list)
        _ = generator.generateXML(view_data_list)

    return check


@pytest.fixture
def check_job(scenario, expected_output, jjb_config, registry):
    def check():
        roots = Roots(jjb_config)
        if jjb_config.recursive:
            path_list = [Path(p) for p in utils.recurse_path(str(scenario.in_path))]
        else:
            path_list = [scenario.in_path]
        load_files(jjb_config, roots, path_list)
        registry.set_macros(roots.macros)
        job_data_list = roots.generate_jobs()
        registry.amend_job_dicts(job_data_list)
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

        check_folders(scenario, job_xml_list)

    return check


@pytest.fixture
def check_view(scenario, expected_output, jjb_config, registry):
    def check():
        roots = Roots(jjb_config)
        load_files(jjb_config, roots, [scenario.in_path])
        registry.set_macros(roots.macros)
        view_data_list = roots.generate_views()
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
