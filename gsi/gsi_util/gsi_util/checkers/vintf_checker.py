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
"""Provides class VintfChecker."""

from gsi_util.checkers.check_result import CheckResultItem
import gsi_util.utils.vintf_utils as vintf_utils


class VintfChecker(object):

  _SYSTEM_MANIFEST_XML = '/system/manifest.xml'
  _VENDOR_MATRIX_XML = '/vendor/compatibility_matrix.xml'

  def __init__(self, file_accessor):
    self._file_accessor = file_accessor

  def check(self, check_result):
    fa = self._file_accessor
    with fa.prepare_file(self._SYSTEM_MANIFEST_XML) as manifest, \
        fa.prepare_file(self._VENDOR_MATRIX_XML) as matrix:
      (result, error_message) = vintf_utils.checkvintf(manifest, matrix)
      check_result.append(CheckResultItem('checkvintf', result, error_message))
