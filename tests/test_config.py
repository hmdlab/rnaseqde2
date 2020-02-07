"""
This is test for rnaseqde.utils
"""

import unittest
from glob import glob

import rnaseqde.utils as utils


class TestConfig(unittest.TestCase):
    def test_load_conf(self, relpath='config/assets.yml'):

        configs = glob('config/assets*.yml')

        for c in configs:
            print(f"Checking {c}...")
            conf = utils.load_conf(c)

            # NOTE: Structure: genome-annotation-tool-path(value)
            paths = []
            for a in conf.values():
                for t in a.values():
                    for p in t.values():
                        paths.append(p)

            existences = list(map(utils.exists, paths))

            for p, e in zip(paths, existences):
                print(
                    "{}: {}".format(p,
                                    e
                                    ))

            self.assertTrue(all(existences))


if __name__ == '__main__':
    unittest.main()
