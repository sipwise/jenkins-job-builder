import os
import re


def get_scenarios(fixtures_path):
    """Returns a list of scenarios, each scenario being described
    by two parameters (yaml and xml filenames).
        - content of the fixture .xml file (aka expected)
    """
    scenarios = []
    files = os.listdir(fixtures_path)
    yaml_files = [f for f in files if re.match(r'.*\.yaml$', f)]

    for yaml_filename in yaml_files:
        xml_candidate = re.sub(r'\.yaml$', '.xml', yaml_filename)
        # Make sure the yaml file has a xml counterpart
        if xml_candidate not in files:
            raise Exception(
                "No XML file named '%s' to match " +
                "YAML file '%s'" % (xml_candidate, yaml_filename))

        scenarios.append((yaml_filename, {
            'yaml_filename': yaml_filename, 'xml_filename': xml_candidate
        }))

    return scenarios
