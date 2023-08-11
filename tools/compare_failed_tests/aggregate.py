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

Given several cts reports, where a cts report could be a zip file or
test_result.xml, this script turn them into one or more sets of
information files.
"""

import argparse
import os
import zipfile

import parse_cts_report


def aggregate_reports(report_files, output_dir):
  """Aggregate all report files."""

  builds = {}

  for report_file in report_files:
    xml_path = (
        parse_cts_report.extract_xml_from_zip(report_file, output_dir)
        if zipfile.is_zipfile(report_file)
        else report_file)
    test_info = parse_cts_report.get_test_info_xml(xml_path)

    key = test_info['build_fingerprint']
    report = builds.setdefault(key, parse_cts_report.CtsReport(test_info))

    report.read_test_result_xml(xml_path)

  if os.path.exists(os.path.join(output_dir, 'test_result.xml')):
    os.remove(os.path.join(output_dir, 'test_result.xml'))

  return builds


def main():
  parser = argparse.ArgumentParser()

  parser.add_argument('--report-files', required=True, nargs='+',
                      help=('Path to cts report(s), where a cts report could '
                            'be a zip archive or a xml file.'))
  parser.add_argument('-d', '--output-dir', required=True,
                      help=('Path to the directory to store output files.'))

  args = parser.parse_args()

  report_files = args.report_files
  output_dir = args.output_dir

  if not os.path.exists(output_dir):
    raise FileNotFoundError(f'Output directory {output_dir} does not exist.')

  builds = aggregate_reports(report_files, output_dir)

  for report in builds.values():
    report.output_files(output_dir)


if __name__ == '__main__':
  main()
