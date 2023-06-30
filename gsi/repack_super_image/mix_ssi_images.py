#!/usr/bin/env python3
#
# Copyright 2023 - The Android Open Source Project
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

"""Mix SSI system.img, system_ext.img and product.img with other vendor images.

Example:
./development/gsi/repack_super_image/mix_ssi_images.py \
    --vendor-target-files aosp_cf_arm64_phone-img.zip \
    --ssi-target-files framework-target_files.zip \
    --misc-info misc_info.txt \
    --otatools otatools.zip \
    --output-dir ./output

or

./development/gsi/repack_super_image/mix_ssi_images.py \
    --vendor-files-dir out/target/product/vsoc_arm64/ \
    --ssi-images-dir out/target/product/xssi/IMAGES/
"""

import argparse
import os
import shutil
import subprocess
import tempfile

import repack_super_image

def add_arguments(parser):
  vendor_args_group = parser.add_mutually_exclusive_group(required=True)
  vendor_args_group.add_argument('--vendor-target-files',
                                 help='The target files of the vendor images '
                                      'to be mixed with the given SSI.')
  vendor_args_group.add_argument('--vendor-files-dir',
                                 help='The directory of the vendor images and '
                                      'misc_info.txt to be mixed with the '
                                      'given SSI. '
                                      'Caution: super.img and vbmeta.img under'
                                      ' this directory will be modified.')
  ssi_args_group = parser.add_mutually_exclusive_group(required=True)
  ssi_args_group.add_argument('--ssi-target-files',
                              help='The SSI framework target files.')
  ssi_args_group.add_argument('--ssi-images-dir',
                              help='The SSI images directory.')
  parser.add_argument('--otatools',
                      help='The otatools.zip for mixing images. '
                           'Default: {args.vendor_files_dir}/otatools.zip.')
  parser.add_argument('--misc-info',
                      help='The vendor misc_info.txt for mixing images. '
                           'Default: {args.vendor_files_dir}/misc_info.txt.')
  parser.add_argument('--output-dir',
                      help='The output directory for the mixed image. '
                           'Default: args.vendor_files_dir.')


def unzip_ssi_images(ssi_target_files, output_dir):
  """Unzip SSI images from the target files zipfile."""
  if not os.path.exists(ssi_target_files):
    raise FileNotFoundError(f'{ssi_target_files} does not exist.')
  cmd = ['unzip', ssi_target_files, 'IMAGES/*', '-d', output_dir]
  print(cmd)
  subprocess.check_call(cmd)
  return os.path.join(output_dir, 'IMAGES')


def unzip_super_images(vendor_img_artifact, output_dir):
  """Unzip super.img from the image artifact zipfile."""
  if not os.path.exists(vendor_img_artifact):
    raise FileNotFoundError(f'{vendor_img_artifact} does not exist.')
  cmd = ['unzip', vendor_img_artifact, 'super.img', '-d', output_dir]
  print(cmd)
  subprocess.check_call(cmd)
  return os.path.join(output_dir, 'super.img')


def collect_ssi_images(ssi_images_dir):
  """Collect system, system_ext and product images for mixing."""
  ssi_imgs = dict()
  collect_partitions = ['system', 'system_ext', 'product']
  for part in collect_partitions:
    img_path = os.path.join(ssi_images_dir, f'{part}.img')
    if not os.path.exists(img_path):
      raise FileNotFoundError(f'{img_path} does not exist.')
    ssi_imgs[part] = img_path
  return ssi_imgs


def main():
  parser = argparse.ArgumentParser()
  add_arguments(parser)
  args = parser.parse_args()

  output_dir = args.output_dir if args.output_dir else args.vendor_files_dir
  if not output_dir:
    raise ValueError('output directory is not set.')
  print(f'Output directory {output_dir}')

  repacker = None
  temp_dirs = []
  tempfile.tempdir = output_dir

  try:
    ssi_images_dir = args.ssi_images_dir
    if not ssi_images_dir:
      temp_dir = tempfile.mkdtemp(prefix='ssi_images_')
      temp_dirs.append(temp_dir)
      ssi_images_dir = unzip_ssi_images(args.ssi_target_files, temp_dir)

    vendor_otatools = args.otatools
    vendor_misc_info = args.misc_info
    if args.vendor_files_dir:
      vendor_files_dir = args.vendor_files_dir
      if not vendor_otatools:
        vendor_otatools = os.path.join(vendor_files_dir, 'otatools.zip')
      if not vendor_misc_info:
        vendor_misc_info = os.path.join(vendor_files_dir, 'misc_info.txt')
      super_img = os.path.join(vendor_files_dir, 'super.img')
    else:
      # Do not remove this temporary directory since this is the mixed output
      temp_dir = tempfile.mkdtemp(prefix='vendor_images_')
      vendor_files_dir = temp_dir
      super_img = unzip_super_images(args.vendor_target_files, temp_dir)

    if not vendor_misc_info or not os.path.exists(vendor_misc_info):
      raise FileNotFoundError(f'{vendor_misc_info} does not exist.')
    if not os.path.exists(super_img):
      raise FileNotFoundError(f'{super_img} does not exist.')
    if not vendor_otatools or not os.path.exists(vendor_otatools):
      raise FileNotFoundError(f'{vendor_otatools} does not exist.')

    mix_part_imgs = collect_ssi_images(ssi_images_dir)
    repacker = repack_super_image.SuperImageRepacker(super_img,
                                                     vendor_otatools)
    repacker.unzip_temp_ota_tools_dir()
    if repack_super_image.is_sparse_image(super_img):
      super_img = repacker.unsparse_super_img()
    unpacked_part_imgs = repacker.unpack_super_img(super_img)
    rewritten_misc_info = repacker.create_misc_info(
        vendor_misc_info, mix_part_imgs, unpacked_part_imgs)
    repacker.build_super_img(rewritten_misc_info)
    print(f'Created mixed super.img at {repacker.super_img}')

    avbtool_path = os.path.join(repacker.ota_tools, 'bin', 'avbtool')
    vbmeta_img = os.path.join(vendor_files_dir, 'vbmeta.img')
    subprocess.check_call([avbtool_path, 'make_vbmeta_image',
                           '--flag', '2', '--output', vbmeta_img])
    print(f'Created vbmeta.img at {vbmeta_img}')
  finally:
    if repacker:
      repacker.clean()
    for temp_dir in temp_dirs:
      shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
  main()
