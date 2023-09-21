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
import os
import tempfile
import unittest
import compare_cts_reports
import parse_cts_report


class TestParse(unittest.TestCase):

  def test_one_way(self):
    with tempfile.TemporaryDirectory() as temp_dir:
      ctsreports = [
          parse_cts_report.parse_report_file('testdata/test_result_1.xml'),
          parse_cts_report.parse_report_file('testdata/test_result_2.xml'),
      ]
      csvfile = os.path.join(temp_dir, 'one_way_diff.csv')
      compare_cts_reports.one_way_compare(ctsreports, csvfile)

      self.check_file(temp_dir, 'one_way_diff.csv')

  def test_two_way(self):
    with tempfile.TemporaryDirectory() as temp_dir:
      ctsreports = [
          parse_cts_report.parse_report_file('testdata/test_result_1.xml'),
          parse_cts_report.parse_report_file('testdata/test_result_2.xml'),
      ]
      csvfile = os.path.join(temp_dir, 'two_way_diff.csv')
      compare_cts_reports.two_way_compare(ctsreports, csvfile)

      self.check_file(temp_dir, 'two_way_diff.csv')

  def test_n_way(self):
    with tempfile.TemporaryDirectory() as temp_dir:
      ctsreports = [
          parse_cts_report.parse_report_file('testdata/test_result_1.xml'),
          parse_cts_report.parse_report_file('testdata/test_result_2.xml'),
      ]
      csvfile = os.path.join(temp_dir, 'n_way_diff.csv')
      compare_cts_reports.n_way_compare(ctsreports, csvfile)

      self.check_file(temp_dir, 'n_way_diff.csv')

  def check_file(self, dir_name, file_name):
    file = os.path.join(dir_name, file_name)
    sample = os.path.join('testdata/compare', file_name)


if __name__ == '__main__':
  unittest.main()
