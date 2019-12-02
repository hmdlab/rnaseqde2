"""
This is test for rnaseqde.utils
"""

import os
import unittest

import rnaseqde.utils


class TestUtils(unittest.TestCase):
    def test_to_abspath(self):
        root_path = os.path.dirname(rnaseqde.utils.__file__)
        relpath = 'foo'

        expected = os.path.join(root_path, relpath)
        actual = rnaseqde.utils.to_abspath(relpath)

        self.assertEqual(expected, actual)

    def test_load_conf(self):
        relpath = '../test/assets.yml'

        conf = rnaseqde.utils.load_conf(relpath)

        expected = 'path_to_index'
        actual = conf['references']['grch38']
        self.assertEqual(expected, actual)

        expected = 'path_to_gtf'
        actual = conf['annotations']['grch38']['gencode']
        self.assertEqual(expected, actual)

    def test_basename_replaced_ext(self):
        str = 'foo.bar.baz'

        expected = 'foo.bar.qux'
        actual = rnaseqde.utils.basename_replaced_ext('.baz', '.qux', str)

        self.assertEqual(expected, actual)

    def test_str_camel_cased(self):
        class_name = 'foo_bar_baz'

        expected = 'fooBarBaz'
        actual = rnaseqde.utils.str_camel_cased(class_name)

        self.assertEqual(expected, actual)

    def test_str_snake_cased(self):
        class_name = 'FooBarBaz'

        expected = 'foo_bar_baz'
        actual = rnaseqde.utils.str_snake_cased(class_name)

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
