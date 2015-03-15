import xml.etree.ElementTree as XML

from jenkins_jobs.errors import JenkinsJobsException


def config_file_provider_builder(xml_parent, data):
    """Builder / Wrapper helper"""
    xml_files = XML.SubElement(xml_parent, 'managedFiles')

    files = data.get('files', [])
    for file in files:
        xml_file = XML.SubElement(xml_files, 'org.jenkinsci.plugins.'
                                  'configfiles.buildwrapper.ManagedFile')
        file_id = file.get('file-id')
        if file_id is None:
            raise JenkinsJobsException("file-id is required for each "
                                       "managed configuration file")
        XML.SubElement(xml_file, 'fileId').text = str(file_id)
        XML.SubElement(xml_file, 'targetLocation').text = \
            file.get('target', '')
        XML.SubElement(xml_file, 'variable').text = \
            file.get('variable', '')


def config_file_provider_settings(xml_parent, data):
    settings = {
        'default-settings':
        'jenkins.mvn.DefaultSettingsProvider',
        'settings':
        'jenkins.mvn.FilePathSettingsProvider',
        'config-file-provider-settings':
        'org.jenkinsci.plugins.configfiles.maven.job.MvnSettingsProvider',
        'default-global-settings':
        'jenkins.mvn.DefaultGlobalSettingsProvider',
        'global-settings':
        'jenkins.mvn.FilePathGlobalSettingsProvider',
        'config-file-provider-global-settings':
        'org.jenkinsci.plugins.configfiles.maven.job.'
        'MvnGlobalSettingsProvider',
    }

    if 'settings' in data:
        # Support for Config File Provider
        settings_file = str(data['settings'])
        if settings_file.startswith(
            'org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig'):
            lsettings = XML.SubElement(
                xml_parent, 'settings',
                {'class': settings['config-file-provider-settings']})
            XML.SubElement(lsettings, 'settingsConfigId').text = settings_file
        else:
            lsettings = XML.SubElement(
                xml_parent, 'settings',
                {'class': settings['settings']})
            XML.SubElement(lsettings, 'path').text = settings_file
    else:
        XML.SubElement(xml_parent, 'settings',
                       {'class': settings['default-settings']})

    if 'global-settings' in data:
        # Support for Config File Provider
        global_settings_file = str(data['global-settings'])
        if global_settings_file.startswith(
                'org.jenkinsci.plugins.configfiles.maven.'
                'GlobalMavenSettingsConfig'):
            gsettings = XML.SubElement(
                xml_parent, 'globalSettings',
                {'class': settings['config-file-provider-global-settings']})
            XML.SubElement(
                gsettings,
                'settingsConfigId').text = global_settings_file
        else:
            gsettings = XML.SubElement(xml_parent, 'globalSettings',
                                       {'class': settings['global-settings']})
            XML.SubElement(gsettings, 'path').text = global_settings_file
    else:
        XML.SubElement(xml_parent, 'globalSettings',
                       {'class': settings['default-global-settings']})
