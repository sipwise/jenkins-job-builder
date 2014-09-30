import xml.etree.ElementTree as XML


def appendXmlConfig(toXmlNode, configDef):
    params = XML.SubElement(toXmlNode,
                            'hudson.plugins.git.'
                            'GitRevisionBuildParameters')

    combineQueuedCommits = 'false'
    try:
        # If git-revision is a boolean, the get() will
        # throw an AttributeError
        if configDef.get('combine-queued-commits'):
            combineQueuedCommits = 'true'
    except AttributeError:
        pass

    properties = XML.SubElement(params, 'combineQueuedCommits')
    properties.text = combineQueuedCommits