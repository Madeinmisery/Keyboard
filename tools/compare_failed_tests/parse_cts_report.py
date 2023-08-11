#!/usr/bin/python3
#
# Copyright (C) 2023 The Android Open Source Project
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
"""Aggregate cts reports into information files.

Given several cts reports, this script turn them into one or more sets of
information files.
"""

import argparse
import csv
import json
import os
import shutil
import xml.etree.ElementTree as ET
import zipfile


# TODO(b/293809772): Logging test result.
# TODO(b/293809772): Aggregate several CTS reports.


class Report:
  """Class to record the test result a cts report."""

  # Constructor method
  def __init__(self, info):
    self.info = info
    self.result_tree = {}
    self.module_summary = {}

  def get_test_status(self, module_name, abi, testcase_name, test_name):
    """Get result from the report class."""

    if module_name not in self.result_tree:
      return None
    abis = self.result_tree[module_name]

    if abi not in abis:
      return None
    testcases = abis[abi]

    if testcase_name not in testcases:
      return None
    tests = testcases[testcase_name]

    if test_name not in tests:
      return None

    return tests[test_name]

  def set_test_status(self, module_name, abi, testcase_name, test_name, result):
    """Set result to the report class."""

    previous = self.get_test_status(module_name, abi, testcase_name, test_name)
    if previous is None:
      abis = self.result_tree.setdefault(module_name, {})
      testcases = abis.setdefault(abi, {})
      tests = testcases.setdefault(testcase_name, {})
      tests[test_name] = result

      module_summary = self.module_summary.setdefault(module_name, {})
      summary = module_summary.setdefault(abi, self.ModuleSummary())
      summary.counter[result] += 1
    else:
      summary = self.module_summary[module_name][abi]
      if summary.result_list.find(result) < summary.result_list.find(previous):
        tests[test_name] = result
        summary[previous] -= 1
        summary[result] += 1

  class ModuleSummary:
    """Record the result summary of each (module, abi) pair."""

    def __init__(self):
      self.result_list = ['pass',
                          'fail',
                          'IGNORED',
                          'ASSUMPTION_FAILURE',
                          'TEST_ERROR',
                          'TEST_STATUS_UNSPECIFIED',]
      self.counter = {}
      self.reset_counter()

    def reset_counter(self):
      self.counter = {
          'pass': 0,
          'fail': 0,
          'IGNORED': 0,
          'ASSUMPTION_FAILURE': 0,
          'TEST_ERROR': 0,
          'TEST_STATUS_UNSPECIFIED': 0,
      }

    def print_summary(self):
      for key in self.result_list:
        print(f'{key}: {self.counter[key]}')
        print()

    def summary_list(self):
      return [self.counter[type] for type in self.result_list]


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
  """Parse the path into xml tag and attribute name."""
  first_dot = attrib_path.index('.')
  tags = attrib_path[:first_dot].split('::')
  attr_name = attrib_path[first_dot+1:]
  return tags, attr_name


def get_test_info_xml(test_result_path):
  """Get test info from xml file."""

  tree = ET.parse(test_result_path)
  root = tree.getroot()

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

  info = test_result.info

  max_key_len = max([len(k) for k in info])
  max_value_len = max([len(info[k]) for k in info])
  table_len = (max_key_len + 2 + max_value_len)

  print('=' * table_len)

  for key in info:
    print(f'{key:<{max_key_len}}  {info[key]}')

  print('=' * table_len)
  print()


def extract_xml_from_zip(zip_file_path, dest_dir):
  """Extract test_result.xml from the zip file."""

  sub_dir_name = os.path.splitext(os.path.basename(zip_file_path))[0]
  xml_path = os.path.join(sub_dir_name, 'test_result.xml')
  extracted_xml = os.path.join(dest_dir, 'test_result.xml')
  with zipfile.ZipFile(zip_file_path) as myzip:
    with myzip.open(xml_path) as source, open(extracted_xml, 'wb') as target:
      shutil.copyfileobj(source, target)
  return extracted_xml


def read_test_result_xml(report, test_result_path):
  """Given the path to a test_result.xml, read that into a Report."""

  tree = ET.parse(test_result_path)
  root = tree.getroot()

  for module in root.iter('Module'):
    module_name = module.attrib['name']
    abi = module.attrib['abi']

    for testcase in module.iter('TestCase'):
      testcase_name = testcase.attrib['name']

      for test in testcase.iter('Test'):
        test_name = test.attrib['name']
        result = test.attrib['result']
        report.set_test_status(module_name, abi,
                               testcase_name, test_name, result)

  return report


def write_to_csv(report, result_csvfile, summary_csvfile):
  """Given a report, write to the csv files.

  Args:
    report: the Report class
    result_csvfile: path to result.csv
    summary_csvfile: path to summary.csv
  """

  result_writer = csv.writer(result_csvfile)
  result_writer.writerow(['module_name', 'abi',
                          'class_name', 'test_name', 'result'])

  summary_writer = csv.writer(summary_csvfile)
  summary_writer.writerow(['module_name', 'abi', 'pass', 'fail', 'IGNORED',
                           'ASSUMPTION_FAILURE', 'TEST_ERROR',
                           'TEST_STATUS_UNSPECIFIED'])

  modules = report.result_tree

  for module_name, abis in modules.items():
    for abi_name, testcases in abis.items():
      module_summary = report.module_summary[module_name][abi_name]

      for testcase_name, tests in testcases.items():
        for test_name, result in tests.items():
          result_writer.writerow([module_name, abi_name,
                                  testcase_name, test_name, result])

      summary = module_summary.summary_list()
      summary_writer.writerow([module_name, abi_name] + summary)


def parse_report_file(report_file, output_dir):
  """Turn one cts report into a Report class."""

  xml_path = (
      extract_xml_from_zip(report_file, output_dir)
      if zipfile.is_zipfile(report_file)
      else report_file)
  test_info = get_test_info_xml(xml_path)

  report = read_test_result_xml(Report(test_info), xml_path)

  return report


def output_files(report, output_dir):
  """Produce output files into the directory."""

  parsed_info_path = os.path.join(output_dir, 'info.json')
  parsed_result_path = os.path.join(output_dir, 'result.csv')
  parsed_summary_path = os.path.join(output_dir, 'summary.csv')

  with open(parsed_info_path, 'w') as info_file:
    info_file.write(json.dumps(report.info, indent=2))

  with (
      open(parsed_result_path, 'w') as result_csvfile,
      open(parsed_summary_path, 'w') as summary_csvfile,
  ):
    write_to_csv(report, result_csvfile, summary_csvfile)

  for f in [parsed_info_path, parsed_result_path, parsed_summary_path]:
    print(f'Parsed output {f}')


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--report-file', required=True,
                      help=('Path to a cts report, where a cts report could '
                            'be a zip archive or a xml file.'))
  parser.add_argument('-d', '--output-dir', required=True,
                      help=('Path to the directory to store output files.'))

  args = parser.parse_args()

  report_file = args.report_file
  output_dir = args.output_dir

  if not os.path.exists(output_dir):
    raise FileNotFoundError(f'Output directory {output_dir} does not exist.')

  output_files(parse_report_file(report_file, output_dir), output_dir)


if __name__ == '__main__':
  main()
