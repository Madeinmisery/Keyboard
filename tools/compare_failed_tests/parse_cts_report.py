#!/usr/bin/python3
#
# Copyright (C) 2022 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#
"""Aggregate CTS reports from zip files to csv files.

Given several zip files, this script extract the test_result.xml's in them
and turn them into csv files.
"""

import argparse
import csv
import json
import os
import xml.etree.ElementTree as ET
import zipfile


# TODO(zoetsou): Logging test result.
# TODO(zoetsou): Allow xml input.
# TODO(zoetsou): Aggregate several CTS reports.


PASS = 'pass'
FAIL = 'fail'
NO_DATA = 'no_data'


class ModuleSummary():
  """Class to record the test result summary of a module."""

  def __init__(self):
    self.counter = {
        'pass': 0,
        'fail': 0,
        'IGNORED': 0,
        'ASSUMPTION_FAILURE': 0,
        'TEST_ERROR': 0,
        'TEST_STATUS_UNSPECIFIED': 0,
    }

  def print_info(self):
    for key, value in self.counter.items():
      print('{}:{} '.format(key, value))
    print()


ATTRS_TO_SHOW = ['Result::Build.build_model',
                 'Result::Build.build_id',
                 'Result::Build.build_fingerprint',
                 'Result::Build.build_device',
                 'Result::Build.build_version_sdk',
                 'Result::Build.build_version_security_patch',
                 'Result::Build.build_board',
                 'Result::Build.build_type',
                 'Result::Build.build_version_release',
                 'Result.suite_name',
                 'Result.suite_version',
                 'Result.suite_plan',
                 'Result.suite_build_number',]


def parse_attrib_path(attrib_path):
  first_dot = attrib_path.index('.')
  tags = attrib_path[:first_dot].split('::')
  attr_name = attrib_path[first_dot+1:]
  return tags, attr_name


def get_test_info(root):
  """Get test info from test_result.xml."""

  test_info = {}

  for attrib_path in ATTRS_TO_SHOW:
    tags, attr_name = parse_attrib_path(attrib_path)
    node = root

    while True:
      tags = tags[1:]
      if tags:
        node = node.find(tags[0])
      else:
        break

    test_info[attr_name] = node.attrib[attr_name]

  return test_info


def print_test_info(test_result):
  """Print test information of the result in table format."""

  info = test_result['info']

  max_key_len = max([len(k) for k in info])
  max_value_len = max([len(info[k]) for k in info])
  table_len = (max_key_len + 2 + max_value_len)

  line_format = '{:{}}  {}'

  print('=' * table_len)

  for key in info:
    print(line_format.format(key, max_key_len, info[key]))

  print('=' * table_len)
  print()


def extract_xml_from_zip(zip_file_path, dir_path):
  """Extract test_result.xml from the zip file."""

  with zipfile.ZipFile(zip_file_path) as myzip:
    myzip.extract('test_result.xml', path=dir_path)


def read_test_result_xml(test_result_path):
  """Given the path to a test_result.xml, read that into a dict."""

  tree = ET.parse(test_result_path)
  root = tree.getroot()

  test_result = {}
  test_result['info'] = get_test_info(root)

  modules = {}
  test_result['modules'] = modules

  for module in root.iter('Module'):
    module_name = module.attrib['name']
    abi_name = module.attrib['abi']

    abis = modules.setdefault(module_name, {})
    testcases = abis.setdefault(abi_name, {})

    for testcase in module.iter('TestCase'):
      testcase_name = testcase.attrib['name']

      tests = testcases.setdefault(testcase_name, {})

      for test in testcase.iter('Test'):
        test_name = test.attrib['name']

        if test_name in tests:
          print('[WARNING] duplicated test:', test_name)

        tests[test_name] = test.attrib['result']

  return test_result


def write_to_csv(test_result, result_csvfile, summary_csvfile):
  """Given a result dict, write to the csv files.

  Args:
    test_result: the dict returned from read_test_result(test_result.xml)
    result_csvfile: path to result.csv
    summary_csvfile: path to summary.csv
  """

  result_writer = csv.writer(result_csvfile)
  result_writer.writerow(['module', 'abi', 'testcase', 'test', 'result'])

  summary_writer = csv.writer(summary_csvfile)
  summary_writer.writerow(['module', 'abi', 'pass', 'fail', 'IGNORED',
                           'ASSUMPTION_FAILURE', 'TEST_ERROR',
                           'TEST_STATUS_UNSPECIFIED'])

  modules = test_result['modules']

  for module_name, abis in modules.items():
    module_result_summary = ModuleSummary()

    for abi_name, testcases in abis.items():

      for testcase_name, tests in testcases.items():

        for test_name, result in tests.items():

          result_writer.writerow([module_name, abi_name] +
                                 [testcase_name, test_name, result])
          module_result_summary.counter[result] += 1

      row = ([module_name, abi_name] +
             [value for value in module_result_summary.counter.values()])
      summary_writer.writerow(row)


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--report-files', nargs='+',
                      help=('Path to cts report(s), where a cts report could '
                            'be a zip archive or a xml file.'))
  parser.add_argument('-d', '--output-dir', default='temp',
                      help=('path to the directory to store temporary files'))

  args = parser.parse_args()

  dir_path = args.output_dir

  extract_xml_from_zip(args.report_files[0], dir_path)
  test_result = read_test_result_xml(os.path.join(dir_path, 'test_result.xml'))

  print_test_info(test_result)

  with open(os.path.join(dir_path, 'info.json'), 'w') as info_file:
    info_file.write(json.dumps(test_result['info'], indent=2))

  with (
      open(os.path.join(dir_path, 'result.csv'), 'w') as result_csvfile,
      open(os.path.join(dir_path, 'summary.csv'), 'w') as summary_csvfile,
  ):
    write_to_csv(test_result, result_csvfile, summary_csvfile)

  print(os.path.abspath(dir_path))


if __name__ == '__main__':
  main()
