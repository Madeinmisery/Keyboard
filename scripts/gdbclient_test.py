# Copyright 2023 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import gdbclient
import unittest
import copy
import json


class LaunchConfigMergeTest(unittest.TestCase):
    def merge_compare(self, base, to_add, expected):
        actual = copy.deepcopy(base)
        gdbclient.merge_launch_dict(actual, to_add)
        self.assertEqual(actual, expected, f'base={base}, to_add={to_add}')

    def test_add_none(self):
        base = { 'foo' : 1 }
        to_add = None
        expected = { 'foo' : 1 }
        self.merge_compare(base, to_add, expected)

    def test_add_val(self):
        base = { 'foo' : 1 }
        to_add = { 'bar' : 2}
        expected = { 'foo' : 1, 'bar' : 2 }
        self.merge_compare(base, to_add, expected)

    def test_overwrite_val(self):
        base = { 'foo' : 1 }
        to_add = { 'foo' : 2}
        expected = { 'foo' : 2 }
        self.merge_compare(base, to_add, expected)

    def test_add_elem_to_list(self):
        base = { 'foo' : [1] }
        to_add = { 'foo' : 2}
        expected = { 'foo' : [1, 2] }
        self.merge_compare(base, to_add, expected)

    def test_add_list_to_elem(self):
        base = { 'foo' : 1 }
        to_add = { 'foo' : [2]}
        expected = { 'foo' : [1, 2] }
        self.merge_compare(base, to_add, expected)

    def test_merge_lists(self):
        base = { 'foo' : [1, 2] }
        to_add = { 'foo' : [3, 4]}
        expected = { 'foo' : [1, 2, 3, 4] }
        self.merge_compare(base, to_add, expected)

    def test_add_elem_to_dict(self):
        base = { 'foo' : { 'bar' : 1 } }
        to_add = { 'foo' : { 'baz' : 2 } }
        expected = { 'foo' : { 'bar' :  1, 'baz' : 2 } }
        self.merge_compare(base, to_add, expected)

    def test_overwrite_elem_in_dict(self):
        base = { 'foo' : { 'bar' : 1 } }
        to_add = { 'foo' : { 'bar' : 2 } }
        expected = { 'foo' : { 'bar' : 2 } }
        self.merge_compare(base, to_add, expected)

    def test_mergning_dict_and_value_raises(self):
        base = { 'foo' : { 'bar' : 1 } }
        to_add = { 'foo' : 2 }
        with self.assertRaises(Exception):
            gdbclient.merge_launch_dict(base, to_add)

    def test_mergning_value_and_dict_raises(self):
        base = { 'foo' : 2 }
        to_add = { 'foo' : { 'bar' : 1 } }
        with self.assertRaises(Exception):
            gdbclient.merge_launch_dict(base, to_add)

    def test_mergning_dict_and_list_raises(self):
        base = { 'foo' : { 'bar' : 1 } }
        to_add = { 'foo' : [1] }
        with self.assertRaises(Exception):
            gdbclient.merge_launch_dict(base, to_add)

    def test_mergning_list_and_dict_raises(self):
        base = { 'foo' : [1] }
        to_add = { 'foo' : { 'bar' : 1 } }
        with self.assertRaises(Exception):
            gdbclient.merge_launch_dict(base, to_add)


class VsCodeLaunchGeneratorTest(unittest.TestCase):
    def setUp(self):
        # These tests can generate long diffs, so we remove the limit
        self.maxDiff = None

    def test_generate_script(self):
        self.assertEqual(json.loads(gdbclient.generate_vscode_lldb_script(root='/root',
                                                            sysroot='/sysroot',
                                                            binary_name='test',
                                                            port=123,
                                                            solib_search_path=['/path1',
                                                                               '/path2'],
                                                            extra_props=None)),
        {
             'name': '(lldbclient.py) Attach test (port: 123)',
             'type': 'lldb',
             'request': 'custom',
             'relativePathBase': '/root',
             'sourceMap': { '/b/f/w' : '/root', '': '/root', '.': '/root' },
             'initCommands': ['settings append target.exec-search-paths /path1 /path2'],
             'targetCreateCommands': ['target create test',
                                      'target modules search-paths add / /sysroot/'],
             'processCreateCommands': ['gdb-remote 123']
         });

    def test_generate_script_with_extra_props(self):
        extra_props = {
            'initCommands' : 'settings append target.exec-search-paths /path3',
            'processCreateCommands' : ['break main', 'continue'],
            'sourceMap' : { '/test/' : '/root/test'},
            'preLaunchTask' : 'Build'
        }
        self.assertEqual(json.loads(gdbclient.generate_vscode_lldb_script(root='/root',
                                                            sysroot='/sysroot',
                                                            binary_name='test',
                                                            port=123,
                                                            solib_search_path=['/path1',
                                                                               '/path2'],
                                                            extra_props=extra_props)),
        {
             'name': '(lldbclient.py) Attach test (port: 123)',
             'type': 'lldb',
             'request': 'custom',
             'relativePathBase': '/root',
             'sourceMap': { '/b/f/w' : '/root',
                           '': '/root',
                           '.': '/root',
                           '/test/' : '/root/test' },
             'initCommands': [
                 'settings append target.exec-search-paths /path1 /path2',
                 'settings append target.exec-search-paths /path3',
             ],
             'targetCreateCommands': ['target create test',
                                      'target modules search-paths add / /sysroot/'],
             'processCreateCommands': ['gdb-remote 123',
                                       'break main',
                                       'continue'],
             'preLaunchTask' : 'Build'
         });


if __name__ == '__main__':
  unittest.main(verbosity=2)
