from jenkins_jobs.builder import Builder
import os
import shutil
import unittest


class TestRecursiveYamlParsing(unittest.TestCase):
    fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures')
    test_output_path = os.path.join(os.path.dirname(__file__), 'test_output')

    def tearDown(self):
        shutil.rmtree(self.test_output_path)

    def test_recursion(self):
        builder = Builder('http://fakehost', None, None, False)
        jobs_parsed = builder.update_job(
            self.fixtures_path, [], self.test_output_path
        )
        job_list = [job.name for job in jobs_parsed]
        assert 'complete002_1.2' in job_list
