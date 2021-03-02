"""
This is test for rnaseqde.utils
"""

import unittest

import rnaseqde.utils as utils


class TestUtils(unittest.TestCase):
    def test_load_conf(self):
        relpath = 'tests/test.yml'

        conf = utils.load_conf(utils.from_root(relpath))

        expected = 'path_to_baz'
        actual = conf['foo']['bar']
        self.assertEqual(expected, actual)

    def test_basename_replaced_ext(self):
        str = 'foo.bar.baz'

        expected = 'foo.bar.qux'
        actual = utils.basename_replaced_ext('.baz', '.qux', str)

        self.assertEqual(expected, actual)

    def test_camel_cased(self):
        class_name = 'foo_bar_baz'

        expected = 'fooBarBaz'
        actual = utils.camel_cased(class_name)

        self.assertEqual(expected, actual)

    def test_snake_cased(self):
        class_name = 'FooBarBaz'

        expected = 'foo_bar_baz'
        actual = utils.snake_cased(class_name)

        self.assertEqual(expected, actual)

    def test_dictcombine(self):

        dict1 = {
            'foo': 1,
            'bar': 2
            }

        dict2 = {
            'bar': 2,
            'baz': 3
            }

        excepted = {
            'foo': [1],
            'bar': [2, 2],
            'baz': [3]
            }

        actual = utils.dictcombine([dict1, dict2])

        self.assertEqual(excepted, actual)

        excepted = {
            'foo': [1, 0],
            'bar': [2, 2],
            'baz': [0, 3]
            }

        actual = utils.dictcombine([dict1, dict2], default=0)

        self.assertEqual(excepted, actual)


if __name__ == '__main__':
    unittest.main()
