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

"""Mix shared system images with a super image and disable vbmeta.

Example:
./development/gsi/repack_super_image/mix_ssi_with_device_image.py \
    --device-image-files aosp_cf_arm64_phone-img.zip \
    --ssi-files ssi-target_files.zip \
    --misc-info misc_info.txt \
    --otatools otatools.zip \
    --output-dir ./output

or

./development/gsi/repack_super_image/mix_ssi_with_device_image.py \
    --device-image-files out/target/product/vsoc_arm64/ \
    --ssi-files out/target/product/ssi/IMAGES/
"""

import argparse
import os
import shutil
import subprocess
import tempfile
import zipfile

import repack_super_image


SSI_PARTITIONS = ["system", "system_ext", "product"]


def add_arguments(parser):
  parser.add_argument("--device-image-files",
                      default=os.getenv("ANDROID_PRODUCT_OUT"),
                      help="The path to the zipfile or directory containing "
                           "device images to be mixed with the given SSI. "
                           "Caution: If this is a directory, super.img and "
                           "vbmeta.img under this directory will be modified. "
                           "Default: $ANDROID_PRODUCT_OUT")
  parser.add_argument("--ssi-files", required=True,
                      help="The path to the zipfile or directory containing "
                           "shared system images for mixing.")
  parser.add_argument("--otatools",
                      help="The device otatools.zip for mixing images. "
                           "Default: {args.device_image_files}/otatools.zip.")
  parser.add_argument("--misc-info",
                      help="The device misc_info.txt for mixing images. "
                           "Default: {args.device_image_files}/misc_info.txt.")
  parser.add_argument("--output-dir",
                      help="The output directory for the mixed image. "
                           "Default: {args.device_image_files}.")


def unzip_ssi_images(ssi_target_files, output_dir):
  """Unzip shared system images from the target files zipfile."""
  if not os.path.exists(ssi_target_files):
    raise FileNotFoundError(f"{ssi_target_files} does not exist.")
  with zipfile.ZipFile(ssi_target_files) as ssi_zip:
    for part_img in SSI_PARTITIONS:
      ssi_zip.extract(f"IMAGES/{part_img}.img", output_dir)
  return os.path.join(output_dir, "IMAGES")


def unzip_super_images(device_img_artifact, output_dir):
  """Unzip super.img from the device image artifact zipfile."""
  if not os.path.exists(device_img_artifact):
    raise FileNotFoundError(f"{device_img_artifact} does not exist.")
  with zipfile.ZipFile(device_img_artifact) as device_img_zip:
    device_img_zip.extract("super.img", output_dir)
  return os.path.join(output_dir, "super.img")


def collect_ssi(ssi_dir):
  """Collect system, system_ext and product images for mixing."""
  ssi_imgs = dict()
  for part_img in SSI_PARTITIONS:
    img_path = os.path.join(ssi_dir, f"{part_img}.img")
    if not os.path.exists(img_path):
      raise FileNotFoundError(f"{img_path} does not exist.")
    ssi_imgs[part_img] = img_path
  return ssi_imgs


def main():
  parser = argparse.ArgumentParser()
  add_arguments(parser)
  args = parser.parse_args()

  if not args.device_image_files:
    raise ValueError("device image path is not set.")

  output_dir = args.output_dir if args.output_dir else args.device_image_files
  if not os.path.isdir(output_dir):
    raise ValueError(f"output directory {output_dir} is not valid.")
  print(f"Output directory {output_dir}")

  temp_dirs = []
  tempfile.tempdir = output_dir

  try:
    if os.path.isdir(args.ssi_files):
      ssi_dir = args.ssi_files
    else:
      temp_dir = tempfile.mkdtemp(prefix="ssi_")
      temp_dirs.append(temp_dir)
      ssi_dir = unzip_ssi_images(args.ssi_files, temp_dir)

    vendor_otatools = args.otatools
    vendor_misc_info = args.misc_info
    if os.path.isdir(args.device_image_files):
      device_image_dir = args.device_image_files
      super_img = os.path.join(device_image_dir, "super.img")
      if not vendor_otatools:
        vendor_otatools = os.path.join(device_image_dir, "otatools.zip")
      if not vendor_misc_info:
        vendor_misc_info = os.path.join(device_image_dir, "misc_info.txt")
    else:
      device_image_dir = output_dir
      super_img = unzip_super_images(args.device_image_files, device_image_dir)

    if not vendor_otatools or not os.path.exists(vendor_otatools):
      raise FileNotFoundError(f"{vendor_otatools} does not exist.")
    if not vendor_misc_info or not os.path.exists(vendor_misc_info):
      raise FileNotFoundError(f"{vendor_misc_info} does not exist.")
    if not os.path.exists(super_img):
      raise FileNotFoundError(f"{super_img} does not exist.")

    print("Unzip OTA tools.")
    temp_ota_tools_dir = tempfile.mkdtemp(prefix="ota_tools")
    temp_dirs.append(temp_ota_tools_dir)
    with zipfile.ZipFile(vendor_otatools) as ota_tools_zip:
      repack_super_image.unzip_ota_tools(ota_tools_zip, temp_ota_tools_dir)

    mix_part_imgs = collect_ssi(ssi_dir)
    repack_super_image.repack_super_image(temp_ota_tools_dir, vendor_misc_info,
                                          super_img, mix_part_imgs)
    print(f"Created mixed super.img at {super_img}")

    avbtool_path = os.path.join(temp_ota_tools_dir, "bin", "avbtool")
    vbmeta_img = os.path.join(device_image_dir, "vbmeta.img")
    subprocess.check_call([avbtool_path, "make_vbmeta_image",
                           "--flag", "2", "--output", vbmeta_img])
    print(f"Created vbmeta.img at {vbmeta_img}")
  finally:
    for temp_dir in temp_dirs:
      shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
  main()
