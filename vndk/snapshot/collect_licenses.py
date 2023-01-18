#!/usr/bin/env python3
#
# Copyright (C) 2021 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import glob
import logging
import os

import utils

LICENSE_KINDS_PREFIX = 'SPDX-license-identifier-'
LICENSE_KEYWORDS = {
    'Apache-2.0': ('Apache License', 'Version 2.0',),
    'BSD': ('BSD ',),
    'CC0-1.0': ('CC0 Public Domain Dedication license',),
    'FTL': ('FreeType Project LICENSE',),
    'ISC': ('Internet Systems Consortium',),
    'ISC': ('ISC license',),
    'MIT': (' MIT ',),
    'MPL-2.0': ('Mozilla Public License Version 2.0',),
    'MPL': ('Mozilla Public License',),
    'NCSA': ('University of Illinois', 'NCSA',),
    'OpenSSL': ('The OpenSSL Project',),
    'Zlib': ('zlib License',),
}
RESTRICTED_LICENSE_KEYWORDS = {
    'LGPL-3.0': ('LESSER GENERAL PUBLIC LICENSE', 'Version 3,',),
    'LGPL-2.1': ('LESSER GENERAL PUBLIC LICENSE', 'Version 2.1',),
    'LGPL-2.0': ('GNU LIBRARY GENERAL PUBLIC LICENSE', 'Version 2,',),
    'LGPL': ('LESSER GENERAL PUBLIC LICENSE',),
    'GPL-2.0': ('GNU GENERAL PUBLIC LICENSE', 'Version 2,',),
    'GPL': ('GNU GENERAL PUBLIC LICENSE',),
}
SPECIAL_LICENSES = {
    'legacy_notice': ('BLAS', 'PNG', 'IBM-DHCP', 'SunPro', 'Caffe',),
    'legacy_permissive': ('blessing',),
    'SPDX-license-identifier-MIT': ('LicenseRef-MIT-Lucent', 'cURL',)
}


class LicenseCollector(object):
    """ Collect licenses from a VNDK snapshot directory

    This is to collect the license_kinds to be used in license modules.
    It also lists the modules with the restricted licenses.

    Initialize the LicenseCollector with a vndk snapshot directory.
    After run() is called, 'license_kinds' will include the licenses found from
    the snapshot directory.
    'restricted' will have the files that have the restricted licenses.
    """
    def __init__(self, install_dir):
        def read_license_modules():
            available_license_kinds = []
            licenses_android_bp = os.path.join(utils.get_android_build_top(),
                                              'build/soong/licenses/Android.bp')
            with open(licenses_android_bp, 'r') as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    if not line.strip().startswith(
                            'name: "SPDX-license-identifier-'):
                        continue
                    available_license_kinds.append(line.strip()[len(
                            'name: "SPDX-license-identifier-'):-2])
            return available_license_kinds

        self._install_dir = install_dir
        self._paths_to_check = [os.path.join(install_dir,
                                              utils.NOTICE_FILES_DIR_PATH),]
        self._paths_to_check = self._paths_to_check + glob.glob(
                    os.path.join(self._install_dir, '*/include'))

        self.license_kinds = set()
        self.restricted = set()

        self._is_identify_license_tool_available = utils.check_identify_license_tool()
        self.unhandled_licenses = set()
        self.available_licenses = read_license_modules()

    def read_and_check_licenses(self, license_text, license_keywords):
        """ Read the license keywords and check if all keywords are in the file.

        The found licenses will be added to license_kinds set. This function
        will return True if any licenses are found, False otherwise.
        """
        found = False
        for lic, patterns in license_keywords.items():
            for pattern in patterns:
                if pattern not in license_text:
                    break
            else:
                self.license_kinds.add(LICENSE_KINDS_PREFIX + lic)
                found = True
        return found

    def identify_license_with_keywords(self, filepath):
        """ Read a license text file and find the license_kinds.
            This finds the licenses with simple keyword matching.
        """
        with open(filepath, 'r') as file_to_check:
            file_string = file_to_check.read()
            self.read_and_check_licenses(file_string, LICENSE_KEYWORDS)
            if self.read_and_check_licenses(file_string,
                                            RESTRICTED_LICENSE_KEYWORDS):
                self.restricted.add(os.path.basename(filepath))

    def license_kind_map(self, license):
        """ Replace the name of license with those for the license module
        """
        lic = license[len('Supplement:'):] if license.startswith('Supplement:') else license
        if lic in self.available_licenses:
            return LICENSE_KINDS_PREFIX + lic

        for lic_kind in SPECIAL_LICENSES:
            if lic in SPECIAL_LICENSES[lic_kind]:
                return lic_kind

        self.unhandled_licenses.add(lic)
        return 'legacy_unencumbered'

    def interpret_licenses(self, licenses):
        """ Generate a license set after interpreting the library identification.
        """
        license_kinds = set()
        for lic in licenses:
            license_kinds.add(self.license_kind_map(lic))
        return license_kinds

    def identify_license_with_tool(self, path, header):
        """ Read license text files in the path to identify.

        Args:
          path: string, path to read license files. If the path is a directory,
                it reads the files under the directory.
          header: boolean, True to read the head files. It must be false to
                read a single file.
        """
        if not self._is_identify_license_tool_available:
            # identify tool does not exist.
            return

        try:
            licenses = utils.identify_license(path, header)
            self.license_kinds.update(self.interpret_licenses(licenses))
        except:
            logging.debug('Tool skipped')

    def run(self, license_text_path=''):
        """ search licenses in vndk snapshots

        Args:
          license_text_path: path to the license text file to check.
                             If empty, check all license files.
        """
        self.license_kinds.clear()
        if license_text_path == '':
            # check all files
            for path in self._paths_to_check:
                logging.info('Reading {}'.format(path))
                self.identify_license_with_tool(path, header=True)
                for (root, _, files) in os.walk(path):
                    for f in files:
                        self.identify_license_with_keywords(os.path.join(root, f))
        else:
            # check a single file
            logging.info('Reading {}'.format(license_text_path))
            self.identify_license_with_tool(
                os.path.join(self._install_dir,
                             utils.COMMON_DIR_PATH,
                             license_text_path),
                header=False)
            self.identify_license_with_keywords(
                os.path.join(self._install_dir,
                             utils.COMMON_DIR_PATH,
                             license_text_path))
            if not self.license_kinds:
                # Add 'legacy_unencumbered' if no licenses are found.
                self.license_kinds.add('legacy_unencumbered')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'vndk_version',
        type=utils.vndk_version_int,
        help='VNDK snapshot version to check, e.g. "{}".'.format(
            utils.MINIMUM_VNDK_VERSION))
    parser.add_argument(
        '-v',
        '--verbose',
        action='count',
        default=0,
        help='Increase output verbosity, e.g. "-v", "-vv".')
    return parser.parse_args()


def main():
    """ For the local testing purpose.
    """
    ANDROID_BUILD_TOP = utils.get_android_build_top()
    PREBUILTS_VNDK_DIR = utils.join_realpath(ANDROID_BUILD_TOP,
                                             'prebuilts/vndk')
    args = get_args()
    vndk_version = args.vndk_version
    install_dir = os.path.join(PREBUILTS_VNDK_DIR, 'v{}'.format(vndk_version))
    utils.set_logging_config(args.verbose)

    license_collector = LicenseCollector(install_dir)
    license_collector.run()
    print(sorted(license_collector.license_kinds))
    print(sorted(license_collector.restricted))


if __name__ == '__main__':
    main()
