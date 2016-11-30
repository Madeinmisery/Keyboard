#!/usr/bin/python

#
# Copyright 2015, The Android Open Source Project
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
#

"""Tests the Checkstyle script used to run style checks on Java files."""

from StringIO import StringIO
import unittest
import checkstyle
import xml.dom.minidom


TEST_RULE = u'com.puppycrawl.tools.checkstyle.checks.BANANAS'
TEST_SHA = u'0000deadbeef000000deadbeef00deadbeef0000'
TEST_ROOT = u'/usr/local/android/master/framework/support'
TEST_FILE1 = TEST_ROOT + u'/Blarg.java'
TEST_FILE2 = TEST_ROOT + u'/Blarg2.java'
TEST_FILE_NON_JAVA = TEST_ROOT + u'/blarg.cc'
FILE_ADDED = u'A '
FILE_MODIFIED = u'M '
FILE_UNTRACKED = u'??'
OUTPUT1 = ('<?xml version="1.0" encoding="UTF-8"?>'
          '<file>'
          '<error line="82" source="com.puppycrawl.tools.checkstyle.checks.indentation.IndentationCheck"/>'
          '<error line="83" source="com.puppycrawl.tools.checkstyle.checks.indentation.IndentationCheck"/>'
          '<error line="90" source="com.puppycrawl.tools.checkstyle.checks.indentation.IndentationCheck"/>'
          '<error line="99" source="com.puppycrawl.tools.checkstyle.checks.indentation.IndentationCheck"/>'
          '</file>')


def mock_repository_root():
  return TEST_ROOT


def mock_last_commit():
  return TEST_SHA


def mock_modified_files_good(root, tracked_only=False, commit=None):
  if commit:
    return {TEST_FILE1: FILE_MODIFIED, TEST_FILE2: FILE_ADDED}
  return {}


def mock_modified_files_uncommitted(root, tracked_only=False, commit=None):
  if tracked_only and not commit:
    return {TEST_FILE1: FILE_MODIFIED}
  if commit:
    return {TEST_FILE1: FILE_MODIFIED, TEST_FILE2: FILE_ADDED}
  return {}


def mock_modified_files_untracked(root, tracked_only=False, commit=None):
  if not tracked_only:
    return {TEST_FILE1: FILE_UNTRACKED}
  if commit:
    return {TEST_FILE2: FILE_ADDED}
  return {}


def mock_modified_files_non_java(root, tracked_only=False, commit=None):
  if commit:
    return {TEST_FILE1: FILE_MODIFIED, TEST_FILE_NON_JAVA: FILE_ADDED}
  return {}


class TestCheckstyle(unittest.TestCase):

  def setUp(self):
    checkstyle.git.repository_root = mock_repository_root
    checkstyle.git.last_commit = mock_last_commit

  def test_ShouldSkip(self):
    # Skip checks for explicit git commit.
    self.assertFalse(checkstyle._ShouldSkip(
        True, None, 1, TEST_RULE, False, False, None, None))
    self.assertTrue(checkstyle._ShouldSkip(
        True, [], 1, TEST_RULE, False, False, [], []))
    self.assertFalse(checkstyle._ShouldSkip(
        True, [1], 1, TEST_RULE, False, False, [], [1]))
    self.assertFalse(checkstyle._ShouldSkip(
        True, [1, 2, 3], 1, TEST_RULE, False, False, [], [1, 2, 3]))
    self.assertTrue(checkstyle._ShouldSkip(
        True, [1, 2, 3], 4, TEST_RULE, False, False, [], [1, 2, 3]))
    for rule in checkstyle.FORCED_RULES:
      self.assertFalse(checkstyle._ShouldSkip(
          True, [1, 2, 3], 1, rule, False, False, [], [1, 2, 3]))
      self.assertFalse(checkstyle._ShouldSkip(
          True, [1, 2, 3], 4, rule, False, False, [], [1, 2, 3]))

    # Skip checks for explicitly checked files.
    self.assertFalse(checkstyle._ShouldSkip(
        False, None, 1, TEST_RULE, False, False, [], None))
    self.assertFalse(checkstyle._ShouldSkip(
        False, [], 1, TEST_RULE, False, False, [], []))
    self.assertFalse(checkstyle._ShouldSkip(
        False, [1], 1, TEST_RULE, False, False, [], [1]))
    self.assertFalse(checkstyle._ShouldSkip(
        False, [1, 2, 3], 1, TEST_RULE, False, False, [], [1, 2, 3]))
    self.assertFalse(checkstyle._ShouldSkip(
        False, [1, 2, 3], 4, TEST_RULE, False, False, [], [1, 2, 3]))
    for rule in checkstyle.FORCED_RULES:
      self.assertFalse(checkstyle._ShouldSkip(
          False, [1, 2, 3], 1, rule, False, False, [], [1, 2, 3]))
      self.assertFalse(checkstyle._ShouldSkip(
          False, [1, 2, 3], 4, rule, False, False, [], [1, 2, 3]))

    # Skip checks for test classes.
    self.assertFalse(checkstyle._ShouldSkip(
        True, None, 1, TEST_RULE, True, False, [], None))
    self.assertTrue(checkstyle._ShouldSkip(
        True, [], 1, TEST_RULE, True, False, [], []))
    self.assertFalse(checkstyle._ShouldSkip(
        True, [1], 1, TEST_RULE, True, False, [], [1]))
    self.assertFalse(checkstyle._ShouldSkip(
        True, [1, 2, 3], 1, TEST_RULE, True, False, [], [1, 2, 3]))
    self.assertTrue(checkstyle._ShouldSkip(
        True, [1, 2, 3], 4, TEST_RULE, True, False, [], [1, 2, 3]))
    for rule in checkstyle.SKIPPED_RULES_FOR_TEST_FILES:
      self.assertTrue(checkstyle._ShouldSkip(
          True, [1, 2, 3], 1, rule, True, False, [], [1, 2, 3]))
      self.assertTrue(checkstyle._ShouldSkip(
          True, [1, 2, 3], 4, rule, True, False, [], [1, 2, 3]))

    # Test indentation violation forcing
    self.assertFalse(checkstyle._ShouldSkip(
        True, [2], 3, checkstyle.INDENTATION_RULE, False, False, [2, 3], [2]))
    self.assertFalse(checkstyle._ShouldSkip(
        True, [2, 3], 3, checkstyle.INDENTATION_RULE, False, False, [2, 3], [2, 3]))
    self.assertTrue(checkstyle._ShouldSkip(
        True, [2], 4, checkstyle.INDENTATION_RULE, False, False, [2, 3], [2]))
    self.assertTrue(checkstyle._ShouldSkip(
        True, [2], 3, TEST_RULE, False, False, [2, 3], [2]))

    # Test whitespace line change rule forcing
    for rule in checkstyle.WHITESPACE_CHANGE_RULES:
        self.assertFalse(checkstyle._ShouldSkip(
            True, [2], 2, rule, False, False, [], []))
        self.assertTrue(checkstyle._ShouldSkip(
            True, [2], 3, rule, False, False, [], []))
    self.assertTrue(checkstyle._ShouldSkip(
            True, [2], 2, TEST_RULE, False, False, [], []))

  def test_GetModifiedFiles(self):
    checkstyle.git.modified_files = mock_modified_files_good
    out = StringIO()
    files = checkstyle._GetModifiedFiles(mock_last_commit(), out=out)
    output = out.getvalue()
    self.assertEqual(output, '')
    self.assertEqual(files, {TEST_FILE1: FILE_MODIFIED, TEST_FILE2: FILE_ADDED})

  def test_GetModifiedFilesUncommitted(self):
    checkstyle.git.modified_files = mock_modified_files_uncommitted
    with self.assertRaises(SystemExit):
      out = StringIO()
      checkstyle._GetModifiedFiles(mock_last_commit(), out=out)
    self.assertEqual(out.getvalue(), checkstyle.ERROR_UNCOMMITTED)

  def test_GetModifiedFilesUncommittedExplicitCommit(self):
    checkstyle.git.modified_files = mock_modified_files_uncommitted
    out = StringIO()
    files = checkstyle._GetModifiedFiles(mock_last_commit(), True, out=out)
    output = out.getvalue()
    self.assertEqual(output, '')
    self.assertEqual(files, {TEST_FILE1: FILE_MODIFIED, TEST_FILE2: FILE_ADDED})

  def test_GetModifiedFilesNonJava(self):
    checkstyle.git.modified_files = mock_modified_files_non_java
    out = StringIO()
    files = checkstyle._GetModifiedFiles(mock_last_commit(), out=out)
    output = out.getvalue()
    self.assertEqual(output, '')
    self.assertEqual(files, {TEST_FILE1: FILE_MODIFIED})

  def test_WarnIfUntrackedFiles(self):
    checkstyle.git.modified_files = mock_modified_files_untracked
    out = StringIO()
    checkstyle._WarnIfUntrackedFiles(out=out)
    output = out.getvalue()
    self.assertEqual(output, checkstyle.ERROR_UNTRACKED + TEST_FILE1 + '\n\n')

  def test_WarnIfUntrackedFilesNoUntracked(self):
    checkstyle.git.modified_files = mock_modified_files_good
    out = StringIO()
    checkstyle._WarnIfUntrackedFiles(out=out)
    output = out.getvalue()
    self.assertEqual(output, '')

  def test_FilterFiles(self):
    files = {TEST_FILE1: FILE_MODIFIED, TEST_FILE2: FILE_ADDED}
    output = checkstyle._FilterFiles(files, None)
    self.assertEqual(files, output)
    output = checkstyle._FilterFiles(files, ['Blarg2'])
    self.assertEqual({TEST_FILE2: FILE_ADDED}, output)
    output = checkstyle._FilterFiles(files, ['Blarg'])
    self.assertEqual(files, output)
    output = checkstyle._FilterFiles(files, ['FunkyTown'])
    self.assertEqual({}, output)

  def test_GetForcedIndentationErrors(self):
    root = xml.dom.minidom.parseString(OUTPUT1)
    errors = root.getElementsByTagName('error')
    output = checkstyle._GetForcedIndentationErrors(errors, None)
    self.assertEqual([], output)
    output = checkstyle._GetForcedIndentationErrors(errors, [1])
    self.assertEqual([], output)
    output = checkstyle._GetForcedIndentationErrors(errors, [82])
    self.assertEqual([82, 83], output)
    output = checkstyle._GetForcedIndentationErrors(errors, [83])
    self.assertEqual([82, 83], output)
    output = checkstyle._GetForcedIndentationErrors(errors, [90])
    self.assertEqual([90], output)
    output = checkstyle._GetForcedIndentationErrors(errors, [99])
    self.assertEqual([99], output)
    output = checkstyle._GetForcedIndentationErrors(errors, [90, 99])
    self.assertEqual([90, 99], output)
    output = checkstyle._GetForcedIndentationErrors(errors, [82, 90, 99])
    self.assertEqual([82, 83, 90, 99], output)

if __name__ == '__main__':
  unittest.main()
