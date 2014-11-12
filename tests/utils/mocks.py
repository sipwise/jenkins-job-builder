# These are mock helpers intended to help stub standard library functions.

os_walk_return_values = {
    '/jjb_projects': [
        ('/jjb_projects', ('dir1', 'dir2', 'dir3'), ()),
        ('/jjb_projects/dir1', ('bar',), ()),
        ('/jjb_projects/dir2', ('baz',), ()),
        ('/jjb_projects/dir3', (), ()),
        ('/jjb_projects/dir1/bar', (), ()),
        ('/jjb_projects/dir2/baz', (), ()),
    ],
    '/jjb_templates': [
        ('/jjb_templates', ('dir1', 'dir2', 'dir3'), ()),
        ('/jjb_templates/dir1', ('bar',), ()),
        ('/jjb_templates/dir2', ('baz',), ()),
        ('/jjb_templates/dir3', (), ()),
        ('/jjb_templates/dir1/bar', (), ()),
        ('/jjb_templates/dir2/baz', (), ()),
    ],
    '/jjb_macros': [
        ('/jjb_macros', ('dir1', 'dir2', 'dir3'), ()),
        ('/jjb_macros/dir1', ('bar',), ()),
        ('/jjb_macros/dir2', ('baz',), ()),
        ('/jjb_macros/dir3', (), ()),
        ('/jjb_macros/dir1/bar', (), ()),
        ('/jjb_macros/dir2/baz', (), ()),
    ],
}

def os_walk_side_effects(path_name, topdown):
    return os_walk_return_values[path_name]
