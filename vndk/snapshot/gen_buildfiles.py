#!/usr/bin/env python
#
# Copyright (C) 2017 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys


class GenBuildFile(object):
    """Generates Android.mk and Android.bp for prebuilts/vndk/v{version}."""

    INDENT = '    '
    ETC_LIST = ['ld.config.txt', 'llndk.libraries.txt', 'vndksp.libraries.txt']

    # TODO(b/70312118): Parse from soong build system
    RELATIVE_INSTALL_PATHS = {
        'android.hidl.memory@1.0-impl.so': 'hw'
    }

    def __init__(self, install_dir, vndk_version):
        """GenBuildFile constructor.

        Args:
          install_dir: string, absolute path to the prebuilts/vndk/v{version}
            directory where the build files will be generated.
          vndk_version: int, VNDK snapshot version (e.g., 27, 28)
        """
        self._install_dir = install_dir
        self._vndk_version = vndk_version
        self._mkfile = os.path.join(install_dir, 'Android.mk')
        self._bpfile = os.path.join(install_dir, 'Android.bp')
        self._vndk_core = self._parse_lib_list('vndkcore.libraries.txt')
        self._vndk_sp = self._parse_lib_list('vndksp.libraries.txt')
        self._vndk_private = self._parse_lib_list('vndkprivate.libraries.txt')

    def _parse_lib_list(self, txt_filename):
        """Returns a sorted union list of libraries found in provided filenames.

        Args:
          txt_filename: string, file name in VNDK snapshot
        """
        prebuilt_list = []
        txts = find(self._install_dir, [txt_filename])
        for txt in txts:
            path_to_txt = os.path.join(self._install_dir, txt)
            with open(path_to_txt, 'r') as f:
                prebuilts = f.read().strip().split('\n')
                for prebuilt in prebuilts:
                    if prebuilt not in prebuilt_list:
                        prebuilt_list.append(prebuilt)

        return sorted(prebuilt_list)

    def generate_android_mk(self):
        """Autogenerates Android.mk."""

        etc_buildrules = []
        for prebuilt in self.ETC_LIST:
            etc_buildrules.append(self._gen_etc_prebuilt(prebuilt))

        with open(self._mkfile, 'w') as mkfile:
            mkfile.write(self._gen_autogen_msg('#'))
            mkfile.write('\n')
            mkfile.write('LOCAL_PATH := $(call my-dir)\n')
            mkfile.write('\n')
            mkfile.write('\n\n'.join(etc_buildrules))
            mkfile.write('\n')

    def generate_android_bp(self):
        """Autogenerates Android.bp."""

        vndk_core_buildrules = self._gen_vndk_shared_prebuilts(
            self._vndk_core, False)
        vndk_sp_buildrules = self._gen_vndk_shared_prebuilts(
            self._vndk_sp, True)

        with open(self._bpfile, 'w') as bpfile:
            bpfile.write(self._gen_autogen_msg('/'))
            bpfile.write('\n')
            bpfile.write(self._gen_bp_phony())
            bpfile.write('\n')
            bpfile.write('\n'.join(vndk_core_buildrules))
            bpfile.write('\n'.join(vndk_sp_buildrules))

    def _gen_autogen_msg(self, comment_char):
        return ('{0}{0} THIS FILE IS AUTOGENERATED BY '
                'development/vndk/snapshot/gen_buildfiles.py\n'
                '{0}{0} DO NOT EDIT\n'.format(comment_char))

    def _get_versioned_name(self, prebuilt, is_etc):
        """Returns the VNDK version-specific module name for a given prebuilt.

        The VNDK version-specific module name is defined as follows:
        For a VNDK shared library: "libfoo.so" -> "libfoo.vndk.{version}.vendor"
        For an ETC text file: "foo.txt" -> "foo.{version}.txt"

        Args:
          prebuilt: string, name of the prebuilt object
          is_etc: bool, True if the LOCAL_MODULE_CLASS of prebuilt is 'ETC'
        """
        name, ext = os.path.splitext(prebuilt)
        if is_etc:
            if ext != '.txt':
                print('Error: ".txt" is the expected file extension for ETC '
                      'prebuilts.')
                sys.exit(1)
            versioned_name = '{}.{}{}'.format(name, self._vndk_version, ext)
        else:
            versioned_name = '{}.vndk.{}.vendor'.format(
                name, self._vndk_version)

        return versioned_name

    def _gen_etc_prebuilt(self, prebuilt):
        """Generates build rule for an ETC prebuilt.

        Args:
          prebuilt: string, name of ETC prebuilt object
        """

        etc_path = find(self._install_dir, prebuilt)[0]
        etc_sub_path = etc_path[etc_path.index('/') + 1:]

        return (
            '#######################################\n'
            '# {prebuilt}\n'
            'include $(CLEAR_VARS)\n'
            'LOCAL_MODULE := {versioned_name}\n'
            'LOCAL_SRC_FILES := arch-$(TARGET_ARCH)-$(TARGET_ARCH_VARIANT)/'
            '{etc_sub_path}\n'
            'LOCAL_MODULE_CLASS := ETC\n'
            'LOCAL_MODULE_PATH := $(TARGET_OUT_ETC)\n'
            'LOCAL_MODULE_STEM := $(LOCAL_MODULE)\n'
            'include $(BUILD_PREBUILT)\n'.format(
                prebuilt=prebuilt,
                versioned_name=self._get_versioned_name(prebuilt, True),
                etc_sub_path=etc_sub_path))

    def _gen_bp_phony(self):
        """Generates build rule for phony package 'vndk_v{version}'."""

        required = []

        for prebuilts_list in (self._vndk_core, self._vndk_sp):
            for prebuilt in prebuilts_list:
                required.append(self._get_versioned_name(prebuilt, False))

        for prebuilt in self.ETC_LIST:
            required.append(self._get_versioned_name(prebuilt, True))

        required_str = ['"{}",'.format(prebuilt) for prebuilt in required]
        required_formatted = '\n{ind}{ind}'.format(
            ind=self.INDENT).join(required_str)
        required_buildrule = ('{ind}required: [\n'
                              '{ind}{ind}{required_formatted}\n'
                              '{ind}],\n'.format(
                                  ind=self.INDENT,
                                  required_formatted=required_formatted))

        return ('phony {{\n'
                '{ind}name: "vndk_v{ver}",\n'
                '{required_buildrule}'
                '}}\n'.format(
                    ind=self.INDENT,
                    ver=self._vndk_version,
                    required_buildrule=required_buildrule))

    def _gen_vndk_shared_prebuilts(self, prebuilts, is_vndk_sp):
        """Returns list of build rules for given prebuilts.

        Args:
          prebuilts: list of VNDK shared prebuilts
          is_vndk_sp: bool, True if prebuilts are VNDK_SP libs
        """
        build_rules = []
        for prebuilt in prebuilts:
            build_rules.append(
                self._gen_vndk_shared_prebuilt(prebuilt, is_vndk_sp))
        return build_rules

    def _gen_vndk_shared_prebuilt(self, prebuilt, is_vndk_sp):
        """Returns build rule for given prebuilt.

        Args:
          prebuilt: string, name of prebuilt object
          is_vndk_sp: bool, True if prebuilt is a VNDK_SP lib
        """
        def get_arch_srcs(prebuilt):
            """Returns build rule for arch specific srcs.

            e.g.,
            arch: {
                arm: {
                    srcs: ["..."]
                },
                arm64: {

                },
                ...
            }

            Args:
              prebuilt: string, name of prebuilt object
            """
            arch_srcs = '{ind}arch: {{\n'.format(ind=self.INDENT)
            src_paths = find(self._install_dir, [prebuilt])
            # if len(src_paths) < 4:
            #     print prebuilt, src_paths
            for src in sorted(src_paths):
                arch_srcs += ('{ind}{ind}{arch}: {{\n'
                              '{ind}{ind}{ind}srcs: ["{src}"],\n'
                              '{ind}{ind}}},\n'.format(
                                  ind=self.INDENT,
                                  arch=arch_from_path(src),
                                  src=src))
            arch_srcs += '{ind}}},\n'.format(ind=self.INDENT)
            return arch_srcs

        def get_rel_install_path(prebuilt):
            """Returns build rule for 'relative_install_path'.

            Args:
              prebuilt: string, name of prebuilt object
            """
            rel_install_path = ''
            if prebuilt in self.RELATIVE_INSTALL_PATHS:
                path = self.RELATIVE_INSTALL_PATHS[prebuilt]
                rel_install_path += ('{ind}relative_install_path: "{path}",\n'
                                     .format(ind=self.INDENT, path=path))
            return rel_install_path

        name = os.path.splitext(prebuilt)[0]
        vendor_available = 'false' if prebuilt in self._vndk_private else 'true'
        if is_vndk_sp:
            vndk_sp = '{ind}{ind}support_system_process: true,\n'.format(
                ind=self.INDENT)
        else:
            vndk_sp = ''
        arch_srcs = get_arch_srcs(prebuilt)
        rel_install_path = get_rel_install_path(prebuilt)

        return ('vndk_prebuilt_shared {{\n'
                '{ind}name: "{name}",\n'
                '{ind}version: "{ver}",\n'
                '{ind}vendor_available: {vendor_available},\n'
                '{ind}vndk: {{\n'
                '{ind}{ind}enabled: true,\n'
                '{vndk_sp}'
                '{ind}}},\n'
                '{rel_install_path}'
                '{arch_srcs}'
                '}}\n'.format(
                    ind=self.INDENT,
                    name=name,
                    ver=self._vndk_version,
                    vendor_available=vendor_available,
                    vndk_sp=vndk_sp,
                    rel_install_path=rel_install_path,
                    arch_srcs=arch_srcs))


def find(path, names):
    """Finds a list of files in a directory that match the given names.

    Args:
      path: string, absolute path of directory from which to find files
      names: list of strings, names of the files to find
    """
    found = []
    for root, _, files in os.walk(path):
        for file_name in sorted(files):
            if file_name in names:
                abspath = os.path.abspath(os.path.join(root, file_name))
                rel_to_root = abspath.replace(os.path.abspath(path), '')
                found.append(rel_to_root[1:])  # strip leading /
    return found


def arch_from_path(path):
    """Extracts archfrom given VNDK snapshot path.

    Args:
      path: string, path relative to prebuilts/vndk/v{version}

    Returns:
      arch string, (e.g., "arm" or "arm64" or "x86" or "x86_64")
    """
    return path.split('/')[0].split('-')[1]


def main():
    """For local testing purposes.

    Note: VNDK snapshot must be already installed under
      prebuilts/vndk/v{version}.
    """
    ANDROID_BUILD_TOP = os.getenv('ANDROID_BUILD_TOP')
    if not ANDROID_BUILD_TOP:
        print('Error: Missing ANDROID_BUILD_TOP env variable. Please run '
              '\'. build/envsetup.sh; lunch <build target>\'. Exiting script.')
        sys.exit(1)
    PREBUILTS_VNDK_DIR = os.path.realpath(
        os.path.join(ANDROID_BUILD_TOP, 'prebuilts/vndk'))

    vndk_version = 27  # set appropriately
    install_dir = os.path.join(PREBUILTS_VNDK_DIR, 'v{}'.format(vndk_version))

    buildfile_generator = GenBuildFile(install_dir, vndk_version)
    buildfile_generator.generate_android_mk()
    buildfile_generator.generate_android_bp()


if __name__ == '__main__':
    main()
