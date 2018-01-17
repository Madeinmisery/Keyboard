#!/usr/bin/env python
#
# Copyright 2017 - The Android Open Source Project
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
"""debugfs-related utilities."""

import logging
import re

from gsi_util.utils.cmd_utils import run_command

_DEBUGFS = 'debugfs'


def dump(image_file, filespec, out_file):
  """dump the content of the file filespec to the output file out_file.

  Args:
    image_file: the image file to be query
    filespec: the full file/dictionary in image_file to be copied
    out_file: the output file name in the local
  Returns:
    Return True if success. Otherwise return False
  """
  debugfs_command = 'dump {} {}'.format(filespec, out_file)
  _, _, error = run_command(
      [_DEBUGFS, '-R', debugfs_command, image_file],
      read_stderr=True)
  if re.search('File not found', error):
    logging.debug('image_file() returns False')
    return False

  return True


def get_type(image_file, filespec):
  """get the type of the given filespec.

  Args:
    image_file: the image file to be query
    filespec: the full file/dictionary in image_file to be query
  Returns:
    None if filespec does not exist
    'regular' if filespec is a file
    'directory' if filespec is a directory
  """
  debugfs_command = 'stat {}'.format(filespec)
  _, output, error = run_command(
      [_DEBUGFS, '-R', debugfs_command, image_file],
      read_stdout=True,
      read_stderr=True)
  if re.search('File not found', error):
    logging.debug('get_type() returns None')
    return None

  m = re.search('Type:\\s*([^\\s]+)', output)
  assert m is not None, '{} outputs with an unknown format.'.format(_DEBUGFS)

  ret = m.group(1)
  logging.debug('get_type() returns \'%s\'', ret)

  return ret
