"""
This is test for rnaseqde.utils
"""

import unittest

from rnaseqde.task.base import Task, DictWrapperTask
from rnaseqde.task.align_hisat2 import AlignHisat2Task


class TestTask(unittest.TestCase):
    def test_task(self):

        dict_ = {
            '--hisat2-index': 'foo',
            '--gtf': 'bar',
            '--fastq': ['baz', 'qax']
            }

        driver = DictWrapperTask(dict_, output_dir='tmp')
        AlignHisat2Task([driver])

        for t in AlignHisat2Task.instances:
            print("inputs: {}".format(t.inputs))
            print("outputs: {}".format(t.outputs))


if __name__ == '__main__':
    unittest.main()
