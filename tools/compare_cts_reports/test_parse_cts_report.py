#!/usr/bin/python3

import unittest
import parse_cts_report

class TestParse(unittest.TestCase):
  def test_parse(self):
    report_file = 'testdata/test_result_1.xml'
    report = parse_cts_report.parse_report_file(report_file)

    self.assertEqual(report.get_test_status('module_1', 'arm64-v8a', 'testcase_1', 'test_1'), 'pass')
    self.assertEqual(report.get_test_status('module_1', 'arm64-v8a', 'testcase_1', 'test_2'), 'fail')
    self.assertEqual(report.get_test_status('module_2', 'arm64-v8a', 'testcase_2', 'test_3'), 'pass')
    self.assertEqual(report.get_test_status('module_2', 'arm64-v8a', 'testcase_3', 'test_4'), 'ASSUMPTION_FAILURE')
    self.assertEqual(report.get_test_status('module_2', 'arm64-v8a', 'testcase_3', 'test_5'), 'fail')
    self.assertEqual(report.get_test_status('module_2', 'arm64-v8a', 'testcase_4', 'test_6'), 'IGNORED')
    self.assertEqual(report.get_test_status('module_2', 'arm64-v8a', 'testcase_4', 'test_7'), 'fail')
    self.assertEqual(report.get_test_status('module_2', 'arm64-v8a', 'testcase_4', 'test_8'), 'TEST_STATUS_UNSPECIFIED')
    self.assertEqual(report.get_test_status('module_3', 'arm64-v8a', 'testcase_5', 'test_9'), 'pass')
    self.assertEqual(report.get_test_status('module_3', 'arm64-v8a', 'testcase_5', 'test_10'), 'TEST_ERROR')


if __name__ == '__main__':
  unittest.main()
