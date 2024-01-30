#!/bin/bash

# Copyright (C) 2023 The Android Open Source Project
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

function die() {
  echo "${@}" >&2
  exit 1;
}

function run_cmd_or_die() {
  "${@}" > /dev/null || die "Command failed: ${*}"
}

function select_device() {
  while :; do
    read -r -p "Select a device to install the ${1} app (0-${DEVICE_COUNT}): " INDEX
    [[ "${INDEX}" =~ ^[0-9]+$ ]] && ((INDEX >= 0 && INDEX <= DEVICE_COUNT)) && return "${INDEX}"
  done
}

function install_app() {
  if ! adb -s "${1}" install -r -d -g "${2}" > /dev/null 2>&1; then
    adb -s "${1}" uninstall "com.example.android.vdmdemo.${3}" > /dev/null 2>&1
    run_cmd_or_die adb -s "${1}" install -r -d -g "${2}"
  fi
}

function display_help() {
  echo "Setup helper for the VirtualDeviceManager host and client applications."
  echo ""
  echo "  -s, --host):         Setup the host application on the only device connected via ADB."
  echo "  -c, --client):       Setup the client application on the only device connected via ADB."
  echo "  -cd, --camera_demo): Setup the virtual camera demo application (not installed by default)."
  echo "  -a, --all):          Setup all available demo apps: host, client, demos and camera."
  echo "  -i, --install-only): Only install the selected application. Will not perform any build."
  echo "  -h, --help):         Print this help."
}

function display_available_devices() {
    echo
    echo "Available devices:"
    for i in "${!DEVICE_SERIALS[@]}"; do
      echo -e "${i}: ${DEVICE_SERIALS[${i}]}\t${DEVICE_NAMES[${i}]}"
    done
    echo "${DEVICE_COUNT}: Do not install this app"
    echo
}

function privileged_install() {
  local TARGET_DEVICE_SERIAL="${1}"
  local TARGET_DEVICE_NAME="${2}"
  local APK_DIR="${3}"
  local APK_FILENAME="${4}"
  local PERM_SRC="${5}"
  local PERM_DST="${6}"

  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" root
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" remount -R
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" wait-for-device
  sleep 3  # Even after wait-for-device returns, the device may not be ready so give it some time.
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" root
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" remount
  echo "Installing ${APK_FILENAME} as a privileged app to ${TARGET_DEVICE_NAME}..."
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" shell mkdir -p "${APK_DIR}"
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" push "${OUT}/${APK_DIR}/${APK_FILENAME}" "${APK_DIR}"
  echo 'Copying privileged permissions...'
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" push "${PERM_SRC}" "${PERM_DST}"
  echo 'Rebooting device...'
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" reboot
  run_cmd_or_die adb -s "${TARGET_DEVICE_SERIAL}" wait-for-device
  echo
}


[[ -f build/make/envsetup.sh ]] || die "Run this script from the root of the tree."

INSTALL_HOST=true
INSTALL_CLIENT=true
INSTALL_VIRTUAL_CAMERA=false
PERFORM_BUILD=true
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -h|--help) display_help; exit ;;
        -a|--all) INSTALL_VIRTUAL_CAMERA=true; shift ;;
        -s|--host) INSTALL_CLIENT=false; shift ;;
        -c|--client) INSTALL_HOST=false; shift ;;
        -i|--install-only) PERFORM_BUILD=false; shift ;;
        -cd|--camera_demo) INSTALL_VIRTUAL_CAMERA=true; INSTALL_HOST=false; INSTALL_CLIENT=false; shift;;
        *) echo "Unknown parameter passed: $1"; display_help; exit ;;
    esac
done

DEVICE_COUNT=$(adb devices -l | tail -n +2 | head -n -1 | wc -l)
((DEVICE_COUNT > 0)) || die "No devices found"

DEVICE_SERIALS=( $(adb devices -l | tail -n +2 | head -n -1 | awk '{ print $1 }') )
DEVICE_NAMES=( $(adb devices -l | tail -n +2 | head -n -1 | awk '{ print $4 }') )
HOST_SERIAL=""
CLIENT_SERIAL=""
CAMERA_DEMO_SERIAL=""
CLIENT_INDEX=$DEVICE_COUNT
HOST_INDEX=$DEVICE_COUNT
CAMERA_DEMO_INDEX=$DEVICE_COUNT

if [[ ${INSTALL_HOST} == true ]]; then
  if [[ ${DEVICE_COUNT} -eq 1 ]]; then
    HOST_INDEX=0
  else
    display_available_devices
    select_device "VDM Host"
    HOST_INDEX=$?
  fi
fi
if [[ ${INSTALL_CLIENT} == true ]]; then
  if [[ ${DEVICE_COUNT} -eq 1 ]]; then
    CLIENT_INDEX=0
  else
    display_available_devices
    select_device "VDM Client"
    CLIENT_INDEX=$?
  fi
fi
if [[ ${INSTALL_VIRTUAL_CAMERA} == true ]]; then
  if [[ ${DEVICE_COUNT} -eq 1 ]]; then
    CAMERA_DEMO_INDEX=0
  elif ((HOST_INDEX == DEVICE_COUNT)); then
    display_available_devices
    select_device "Virtual Camera Demo"
    CAMERA_DEMO_INDEX=$?
  else
    CAMERA_DEMO_INDEX=$HOST_INDEX
  fi
fi

if ((HOST_INDEX == DEVICE_COUNT)); then
  echo "Not installing host app."
else
  HOST_SERIAL=${DEVICE_SERIALS[HOST_INDEX]}
  HOST_NAME="${HOST_SERIAL} ${DEVICE_NAMES[HOST_INDEX]}"
  echo "Installing VDM Host apps to ${HOST_NAME}."
fi
if ((CLIENT_INDEX == DEVICE_COUNT)); then
  echo "Not installing client app."
else
  CLIENT_SERIAL=${DEVICE_SERIALS[CLIENT_INDEX]}
  CLIENT_NAME="${CLIENT_SERIAL} ${DEVICE_NAMES[CLIENT_INDEX]}"
  echo "Installing VDM Client app to ${CLIENT_NAME}."
fi
if ((CAMERA_DEMO_INDEX == DEVICE_COUNT)); then
  echo "Not installing camera demo app."
else
  CAMERA_DEMO_SERIAL=${DEVICE_SERIALS[CAMERA_DEMO_INDEX]}
  CAMERA_DEMO_NAME="${CAMERA_DEMO_SERIAL} ${DEVICE_NAMES[CAMERA_DEMO_INDEX]}"
  echo "Installing camera demo app to ${CAMERA_DEMO_NAME}."
fi

APKS_TO_BUILD=""
[[ -n "${HOST_SERIAL}" ]] && APKS_TO_BUILD="${APKS_TO_BUILD} VdmHost VdmDemos"
[[ -n "${CLIENT_SERIAL}" ]] && APKS_TO_BUILD="${APKS_TO_BUILD} VdmClient"
[[ -n "${CAMERA_DEMO_SERIAL}" ]] && APKS_TO_BUILD="${APKS_TO_BUILD} VirtualCameraDemo"
[[ -n "${APKS_TO_BUILD}" ]] || exit 0

if [[ ${PERFORM_BUILD} == true ]];
then
  echo
  echo "Building APKs:${APKS_TO_BUILD}..."
  echo

  source ./build/envsetup.sh || die "Failed to set up environment"
  [[ -n "${ANDROID_BUILD_TOP}" ]] || run_cmd_or_die tapas "${APKS_TO_BUILD}"
  UNBUNDLED_BUILD_SDKS_FROM_SOURCE=true m -j "${APKS_TO_BUILD}" || die "Build failed"
else
  echo "Skipping Build"
fi

if [[ -n "${CLIENT_SERIAL}" ]]; then
  echo
  echo "Installing VdmClient.apk to ${CLIENT_NAME}..."
  install_app "${CLIENT_SERIAL}" "${OUT}/system/app/VdmClient/VdmClient.apk" client
fi

if [[ -n "${HOST_SERIAL}" ]]; then
  echo
  echo "Installing VdmDemos.apk to ${HOST_NAME}..."
  install_app "${HOST_SERIAL}" "${OUT}/system/app/VdmDemos/VdmDemos.apk" demos
  echo

  readonly HOST_PERM_BASENAME=com.example.android.vdmdemo.host.xml
  readonly HOST_PERM_SRC="${ANDROID_BUILD_TOP}/development/samples/VirtualDeviceManager/host/${HOST_PERM_BASENAME}"
  readonly HOST_PERM_DST="/system/etc/permissions/${HOST_PERM_BASENAME}"
  readonly HOST_APK_DIR=/system/priv-app/VdmHost

  echo "Preparing ${HOST_NAME} for privileged VdmHost installation..."
  if adb -s "${HOST_SERIAL}" shell ls "${HOST_APK_DIR}/VdmHost.apk" > /dev/null 2>&1 \
      && adb -s "${HOST_SERIAL}" pull "${HOST_PERM_DST}" "/tmp/${HOST_PERM_BASENAME}" > /dev/null 2>&1 \
      && cmp --silent "/tmp/${HOST_PERM_BASENAME}" "${HOST_PERM_SRC}" \
      && (adb -s "${HOST_SERIAL}" uninstall com.example.android.vdmdemo.host > /dev/null 2>&1 || true) \
      && adb -s "${HOST_SERIAL}" install -r -d -g "${OUT}/${HOST_APK_DIR}/VdmHost.apk" > /dev/null 2>&1; then
    echo "A privileged installation already found, installed VdmHost.apk to ${HOST_NAME}"
    echo
  else
    privileged_install "${HOST_SERIAL}" "${HOST_NAME}" "${HOST_APK_DIR}" \
                       "VdmHost.apk" "${HOST_PERM_SRC}" "${HOST_PERM_DST}"
  fi
fi

if [[ -n "${CAMERA_DEMO_SERIAL}" ]]; then

  readonly CAMERA_PERM_BASENAME=com.example.android.vdmdemo.virtualcamera.xml
  readonly CAMERA_PERM_SRC="${ANDROID_BUILD_TOP}/development/samples/VirtualDeviceManager/virtualcamera/${CAMERA_PERM_BASENAME}"
  readonly CAMERA_PERM_DST="/system/etc/permissions/${CAMERA_PERM_BASENAME}"
  readonly CAMERA_DEMO_APK_DIR=/system/priv-app/VirtualCameraDemo

  echo "Preparing ${CAMERA_DEMO_NAME} for privileged VirtualCameraDemo installation..."
  if adb -s "${CAMERA_DEMO_SERIAL}" shell ls "${CAMERA_DEMO_APK_DIR}/VirtualCameraDemo.apk" > /dev/null 2>&1 \
      && adb -s "${CAMERA_DEMO_SERIAL}" pull "${CAMERA_PERM_DST}" "/tmp/${CAMERA_PERM_BASENAME}" > /dev/null 2>&1 \
      && cmp --silent "/tmp/${CAMERA_PERM_BASENAME}" "${CAMERA_PERM_SRC}" \
      && (adb -s "${CAMERA_DEMO_SERIAL}" uninstall com.example.android.vdmdemo.virtualcamera > /dev/null 2>&1 || true) \
      && adb -s "${CAMERA_DEMO_SERIAL}" install -r -d -g "${OUT}/${CAMERA_DEMO_APK_DIR}/VirtualCameraDemo.apk" > /dev/null 2>&1; then
    echo "A privileged installation already found, installed VirtualCameraDemo.apk to ${CAMERA_DEMO_NAME}"
    echo
  else
    privileged_install "${CAMERA_DEMO_SERIAL}" "${CAMERA_DEMO_NAME}" "${CAMERA_DEMO_APK_DIR}" "VirtualCameraDemo.apk" "${CAMERA_PERM_SRC}" "${CAMERA_PERM_DST}"
  fi
fi

# TODO: the script doesn't work on U - the permissions aren't there. pat's script works though.

echo
echo 'Success!'
echo