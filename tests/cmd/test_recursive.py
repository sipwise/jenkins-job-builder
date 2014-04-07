import os
import mock
import testtools
from jenkins_jobs import cmd


# Testing the cmd module can sometimes result in the CacheStorage class
# attempting to create the cache directory multiple times as the tests
# are run in parallel.  Stub out the CacheStorage to ensure that each
# test can safely create the cache directory without risk of interference.
@mock.patch('jenkins_jobs.builder.CacheStorage', mock.MagicMock)
class CmdRecursive(testtools.TestCase):

    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.listdir')
    def test_recursive_path_option_exclude_pattern(self, listdir_mock,
                                                   isdir_mock):
        """
        Test paths returned by the recursive processing when using pattern
        excludes.

        testing paths
            /jjb_configs/dir1/test1/
            /jjb_configs/dir1/file
            /jjb_configs/dir2/test2/
            /jjb_configs/dir3/bar/
            /jjb_configs/test3/bar/
            /jjb_configs/test3/baz/
        """

        listdir_results = [
            ['dir1', 'dir2', 'dir3', 'test3'],
            ['test1', 'file'],
            ['test2'],
            ['bar'],
        ]

        listdir_mock.side_effect = listdir_results

        isdir_results = [True] * 5 + [False] + [True] * 2
        isdir_mock.side_effect = isdir_results
        paths = ['/jjb_configs'] + \
                [os.path.join('/jjb_configs', p)
                 for p in listdir_results[0][:3]] + \
                ['/jjb_configs/dir3/bar']

        self.assertEqual(paths, cmd.recurse_path('/jjb_configs', ['test*']))
        self.assertEqual(len(isdir_results), isdir_mock.call_count)

    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.listdir')
    def test_recursive_path_option_exclude_absolute(self, listdir_mock,
                                                    isdir_mock):
        """
        Test paths returned by the recursive processing when using absolute
        excludes.

        testing paths
            /jjb_configs/dir1/test1/
            /jjb_configs/dir1/file
            /jjb_configs/dir2/test2/
            /jjb_configs/dir3/bar/
            /jjb_configs/test3/bar/
            /jjb_configs/test3/baz/
        """

        listdir_results = [
            ['dir1', 'dir2', 'dir3', 'test3'],
            ['test2'],
            [],
            ['bar'],
            [],
            ['bar', 'baz'],
        ]

        listdir_mock.side_effect = listdir_results

        isdir_results = [True] * 8
        isdir_mock.side_effect = isdir_results
        paths = ['/jjb_configs',
                 '/jjb_configs/dir2',
                 '/jjb_configs/dir3',
                 '/jjb_configs/test3',
                 '/jjb_configs/dir2/test2',
                 '/jjb_configs/dir3/bar',
                 '/jjb_configs/test3/bar',
                 '/jjb_configs/test3/baz']

        self.assertEqual(paths, cmd.recurse_path('/jjb_configs',
                                                 ['/jjb_configs/dir1']))
        self.assertEqual(len(isdir_results), isdir_mock.call_count)

    @mock.patch('jenkins_jobs.cmd.os.path.isdir')
    @mock.patch('jenkins_jobs.cmd.os.listdir')
    def test_recursive_path_option_exclude_relative(self, listdir_mock,
                                                    isdir_mock):
        """
        Test paths returned by the recursive processing when using relative
        excludes.

        testing paths
            ./jjb_configs/dir1/test/
            ./jjb_configs/dir1/file
            ./jjb_configs/dir2/test/
            ./jjb_configs/dir3/bar/
            ./jjb_configs/test/bar/
            ./jjb_configs/test/baz/
        """

        listdir_results = [
            ['dir1', 'dir2', 'dir3', 'test'],
            ['test', 'file'],
            [],
            ['test'],
            [],
            ['bar'],
            [],
            ['bar', 'baz'],
        ]

        listdir_mock.side_effect = listdir_results

        isdir_results = [True] * 5 + [False] + [True] * 4
        isdir_mock.side_effect = isdir_results
        paths = ['jjb_configs',
                 'jjb_configs/dir1',
                 'jjb_configs/dir2',
                 'jjb_configs/dir3',
                 'jjb_configs/test',
                 'jjb_configs/dir1/test',
                 'jjb_configs/dir2/test',
                 'jjb_configs/dir3/bar',
                 'jjb_configs/test/baz']
        paths = [os.path.join(os.getcwd(), p) for p in paths]

        self.assertEqual(paths, cmd.recurse_path('jjb_configs',
                                                 ['jjb_configs/test/bar']))
        self.assertEqual(len(isdir_results), isdir_mock.call_count)
