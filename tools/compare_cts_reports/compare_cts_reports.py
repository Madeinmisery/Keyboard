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
"""Compare failed tests in CTS/VTS test_result.xml.

Given two report files (A and B), this script compare them in two modes:
  One-way mode: For all the failed tests in A, list the tests and the results in
                both reports.
  Two-way mode: For all the tests in A and B, list the tests and the results in
                both reports. If a test only exists in one report, show NO_DATA
                in another one.
"""

import argparse
import csv
import os
import tempfile

import aggregate_cts_reports


NO_DATA = 'no_data'


def one_way_compare(reports, diff_csv):
  """Compare two reports in One-way Mode.
  
  Given two sets of reports, aggregate them into two reports (A and B).
  Then, list all failed tests in A, and show result of the same test in A and B.

  Args:
    reports: list of reports
    diff_csv: path to csv which stores comparison results
  """

  report_a = reports[0]
  report_b = reports[1]

  with open(diff_csv, 'w') as diff_csvfile:
    diff_writer = csv.writer(diff_csvfile)
    diff_writer.writerow(['module_name', 'abi', 'class_name', 'test_name',
                          'result in A', 'result in B'])

    for module_name, abis in report_a.result_tree.items():
      for abi, test_classes in abis.items():
        for class_name, tests in test_classes.items():
          for test_name, result_in_a in tests.items():
            if report_a.is_fail(result_in_a):
              result_in_b = report_b.get_test_status(module_name, abi,
                                                     class_name, test_name)
              if not result_in_b:
                result_in_b = NO_DATA

              diff_writer.writerow([module_name, abi, class_name, test_name,
                                    result_in_a, result_in_b])


def two_way_compare(reports, diff_csv):
  """Compare two reports in Two-way Mode.
  
  Given two sets of reports, aggregate them into two reports (A and B).
  Then, list all tests and show the results in A and B. If a test result exists
  in only one report, consider the result as NO_DATA in another report.

  Args:
    reports: list of reports
    diff_csv: path to csv which stores comparison results
  """

  report_a = reports[0]
  report_b = reports[1]

  with open(diff_csv, 'w') as diff_csvfile:
    diff_writer = csv.writer(diff_csvfile)
    diff_writer.writerow(['module_name', 'abi', 'class_name', 'test_name',
                          'result in A', 'result in B'])

    for module_name, abis in report_a.result_tree.items():
      for abi, test_classes in abis.items():
        for class_name, tests in test_classes.items():
          for test_name, result_in_a in tests.items():
            result_in_b = report_b.get_test_status(module_name, abi,
                                                   class_name, test_name)
            if not result_in_b:
              result_in_b = NO_DATA

            diff_writer.writerow([module_name, abi, class_name, test_name,
                                  result_in_a, result_in_b])

    for module_name, abis in report_b.result_tree.items():
      for abi, test_classes in abis.items():
        for class_name, tests in test_classes.items():
          for test_name, result_in_b in tests.items():
            result_in_a = report_a.get_test_status(module_name, abi,
                                                   class_name, test_name)
            if not result_in_a:
              result_in_a = NO_DATA
              diff_writer.writerow([module_name, abi, class_name, test_name,
                                    result_in_a, result_in_b])


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--reports', '-r', required=True, nargs='+',
                      help=('Path to cts reports. Each flag -r is followed by'
                            'a group of files to be aggregated as one report.'),
                      action='append')
  parser.add_argument('--mode', '-m', required=True, choices=['1', '2', 'n'],
                      help=('Comparison mode. 1: One-way mode. 2: Two-way mode.'
                            'n: N-way mode.'))
  parser.add_argument('--output-dir', '-d', default='./',
                      help='Directory to store output files.')
  parser.add_argument('--output-files', '-o', action='store_true')

  args = parser.parse_args()

  report_files = args.reports
  mode = args.mode
  output_dir = args.output_dir
  diff_csv = os.path.join(output_dir, 'diff.csv')

  if (mode == '1' or mode == '2') and (len(report_files) != 2):
    msg = ('Two sets of reports are required for one-way and two-way mode.')
    raise UserWarning(msg)
  elif len(report_files) < 2:
    msg = ('N-way mode requires at least two sets of reports.')
    raise UserWarning(msg)

  ctsreports = []
  for report_group in report_files:
    report = aggregate_cts_reports.aggregate_cts_reports(report_group)

    if args.output_files:
      device_name = report.info['build_device']
      sub_dir_name = tempfile.mkdtemp(prefix=f'{device_name}_', dir=output_dir)
      report.output_files(sub_dir_name)

    ctsreports.append(report)

  if args.mode == '1':
    one_way_compare(ctsreports, diff_csv)
  elif args.mode == '2':
    two_way_compare(ctsreports, diff_csv)
  else:
    # TODO(b/292453652): Implement N-way comparison.
    print('Error: Arg --mode must be 1 or 2.')


if __name__ == '__main__':
  main()
