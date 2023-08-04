#!/usr/bin/python3
"""
Aggregate CTS reports from zip files to csv files.

Given several zip files, this script extract the test_result.xml's in them
and turn them into csv files. 
"""

import argparse
import collections
import shutil
import os
import zipfile
import csv
import xml.etree.ElementTree as ET
import json


PASS = 'pass'
FAIL = 'fail'
NO_DATA = 'no_data'

TRUE = 'true'
FALSE = 'false'

class ModuleSummary():
  def __init__(self):
    self.counter = collections.OrderedDict()

  def initialize(self):
    self.counter['pass'] = 0
    self.counter['fail'] = 0
    self.counter['IGNORED'] = 0
    self.counter['ASSUMPTION_FAILURE'] = 0
    self.counter['TEST_ERROR'] = 0
    self.counter['TEST_STATUS_UNSPECIFIED'] = 0

  def print_info(self):
    for key, value in self.counter.items():
      print('{}:{} '.format(key, value))
    print()


ATTRS_TO_SHOW = ['Result::Build.build_model',
                 'Result::Build.build_id',
                 'Result::Build.build_fingerprint',
                 'Result.suite_name',
                 'Result.suite_version',
                 'Result.suite_plan',
                 'Result.suite_build_number',
                 'Result.start_display',
                 'Result::Build.build_abis_32',
                 'Result::Build.build_abis_64',]


def parse_attrib_path(attrib_path):
  first_dot = attrib_path.index('.')
  tags = attrib_path[:first_dot].split('::')
  attr_name = attrib_path[first_dot+1:]
  return tags, attr_name


def get_test_info(root):
  """Get test info from test_result.xml."""

  test_info = collections.OrderedDict()

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
  """Print test infomation of the result in table format."""

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

  zip = zipfile.ZipFile(zip_file_path)
  zip.extract('test_result.xml', path=dir_path)


def get_result(test_result, module_name, testcase_name, test_name):
  """Get result of specific module, testcase and test name."""

  modules = test_result['modules']
  if module_name not in modules:
    return NO_DATA

  testcases = modules[module_name]
  if testcase_name not in testcases:
    return NO_DATA

  tests = testcases[testcase_name]
  if test_name not in tests:
    return NO_DATA

  return [y for x, y in tests[test_name].items()], ', '.join([x + ': ' + y for x, y in tests[test_name].items()])


def read_test_result_xml(test_result_path):
  """Given the path to a test_result.xml, read that into a ordered dict."""

  tree = ET.parse(test_result_path)
  root = tree.getroot()

  test_result = collections.OrderedDict()
  test_result['info'] = get_test_info(root)

  modules = collections.OrderedDict() 
  test_result['modules'] = modules

  for module in root.iter('Module'):
    abi = module.attrib['abi']

    module_name = module.attrib['name']

    if module_name not in modules:
      modules[module_name] = collections.OrderedDict()

    testcases = modules[module_name]

    for testcase in module.iter('TestCase'):
      testcase_name = testcase.attrib['name']

      if testcase_name not in testcases:
        testcases[testcase_name] = collections.OrderedDict()

      tests = testcases[testcase_name]

      for test in testcase.iter('Test'):
        test_name = test.attrib['name']

        if test_name not in tests:
          tests[test_name] = collections.OrderedDict()

        if abi in tests[test_name]:
          print('[WARNING] duplicated test:', test_name)

        tests[test_name][abi] = test.attrib['result']

  return test_result


def write_to_csv(test_result, result_csvfile, summary_csvfile):
  """Given a result dict, list all test results and write to the csv file.
  
  Args:
    test_result: the dict returned from read_test_result(test_result.xml)
    
  Returns:
    string: summary
  """

  result_writer = csv.writer(result_csvfile)
  result_writer.writerow(['module', 'testcase', 'test', 'result'])

  summary_writer = csv.writer(summary_csvfile)
  summary_writer.writerow(['module', 'pass', 'fail', 'IGNORED', 'ASSUMPTION_FAILURE', 'TEST_ERROR', 'TEST_STATUS_UNSPECIFIED'])

  summary = ''

  modules = test_result['modules']

  for module_name, testcases in modules.items():
    module_sub_summary = ''
  
    module_result_summary = ModuleSummary()
    module_result_summary.initialize()

    for testcase_name, tests in testcases.items():
      testcase_sub_summary = ''

      for test_name, result in tests.items():
        result, result_with_abi = get_result(test_result, module_name, testcase_name, test_name)

        testcase_sub_summary += '    ' + test_name + ': ' + result_with_abi + '\n'
        result_writer.writerow([module_name, testcase_name, test_name, result_with_abi])

        for r in result:
          module_result_summary.counter[r] += 1

      if testcase_sub_summary:
        module_sub_summary += '  ' + testcase_name + '\n' + testcase_sub_summary

    if module_sub_summary:
      summary += module_name + '\n' + module_sub_summary + '\n'
      
    # print(module_name)
    # module_result_summary.print_info()
    summary_writer.writerow([module_name] + [value for key, value in module_result_summary.counter.items()])

  return summary


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('-a',  nargs='*', help='path to zip file(s) of the first build')
  parser.add_argument('-d', '--dir', help='path to the directory to store temporary files')

  args = parser.parse_args()

  DIR_PATH = args.dir + '/'

  extract_xml_from_zip(args.a[0], DIR_PATH)
  test_result = read_test_result_xml(DIR_PATH + 'test_result.xml')

  print_test_info(test_result)

  with open(DIR_PATH + 'info.txt', 'w') as info_file:
    info = json.dumps(test_result['info'])
    info_file.write(info)

  with open(DIR_PATH + 'result.csv', 'w') as result_csvfile:
    with open(DIR_PATH + 'summary.csv', 'w') as summary_csvfile:
      summary = write_to_csv(test_result, result_csvfile, summary_csvfile)

    # print(summary)


if __name__ == '__main__':
  main()
