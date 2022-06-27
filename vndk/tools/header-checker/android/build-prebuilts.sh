#!/bin/bash -e

# Copyright 2019 Google Inc. All rights reserved.
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

source "$(dirname "$0")/envsetup.sh"

usage() {
    echo "Usage: $(basename $0) [-t build_target].."
    echo "      Supported build targets for macOS: ${MACOS_SOONG_BINARIES[@]}"
    echo "      Supported build targets for Linux: ${LINUX_SOONG_BINARIES[@]}"
}

UNAME="$(uname)"
case "${UNAME}" in
Linux)
    OS='linux'
    ;;
Darwin)
    OS='darwin'
    ;;
*)
    echo "error: Unknown uname: ${UNAME}"
    exit 1
    ;;
esac

LINUX_SOONG_BINARIES=(
    "bindgen"
    "cxx_extractor"
    "header-abi-linker"
    "header-abi-dumper"
    "header-abi-diff"
    "proto_metadata_plugin"
    "protoc_extractor"
    "versioner"
)

MACOS_SOONG_BINARIES=(
    "versioner"
)

# Targets to be built
if [ "${OS}" = "darwin" ]; then
    SOONG_BINARIES=("${MACOS_SOONG_BINARIES[@]}")
else
    SOONG_BINARIES=("${LINUX_SOONG_BINARIES[@]}")
fi


containsElement () {
    for i in "${SOONG_BINARIES[@]}"
    do
        if [ "$i" == "$1" ] ; then
            echo 1
            exit 0
        fi
    done
    echo 0
}

while getopts "t:" arg; do
    case $arg in
        t) # Check if specified build targets in SOONG_BINARIES
            if [[ $(containsElement ${OPTARG}) -eq 1 ]];
            then
                TARGET_BINARIES+=("$OPTARG")
            else
                echo "build_target ${OPTARG} not supported."
                exit 0
            fi
            ;;
        *) # Display help.
            usage
            exit 0
            ;;
    esac
done
shift $((OPTIND -1))

if [[ ${TARGET_BINARIES[@]} ]]; then
    SOONG_BINARIES=("${TARGET_BINARIES[@]}")
fi

set -ex

if [ -z "${OUT_DIR}" ]; then
    echo "error: Must set OUT_DIR"
    exit 1
fi

TOP=$(pwd)

# Setup Soong configuration
SOONG_OUT="${OUT_DIR}/soong"
SOONG_HOST_OUT="${OUT_DIR}/soong/host/${OS}-x86"
rm -rf "${SOONG_OUT}"
mkdir -p "${SOONG_OUT}"
cat > "${SOONG_OUT}/soong.variables" << __EOF__
{
    "Allow_missing_dependencies": true,
    "HostArch":"x86_64"
}
__EOF__


binaries=()
for name in "${SOONG_BINARIES[@]}"; do
    binaries+=("${SOONG_HOST_OUT}/bin/${name}")
done

libs=()
if [ "${OS}" = "darwin" ]; then
    libs+=("${SOONG_HOST_OUT}/lib64/libc++abi_host.dylib")
fi

# Build binaries and shared libs
build/soong/soong_ui.bash --make-mode --skip-config --soong-only "${binaries[@]}" "${libs[@]}"

# Copy binaries and shared libs
SOONG_DIST="${SOONG_OUT}/dist"
mkdir -p "${SOONG_DIST}/bin"
cp "${binaries[@]}" "${SOONG_DIST}/bin"
cp -R "${SOONG_HOST_OUT}/lib"* "${SOONG_DIST}"

# Copy clang header and share files
CLANG_DIR="prebuilts/clang/host/${OS}-x86/${LLVM_PREBUILTS_VERSION}"
CLANG_LIB_DIR="${CLANG_DIR}/lib64/clang/${LLVM_RELEASE_VERSION}"
CLANG_LIB_DIR_OUT="${SOONG_DIST}/lib64/clang/${LLVM_RELEASE_VERSION}"
mkdir -p "${CLANG_LIB_DIR_OUT}"
cp -R "${CLANG_LIB_DIR}/share" "${CLANG_LIB_DIR_OUT}/share"
cp -R "${CLANG_LIB_DIR}/include" "${CLANG_LIB_DIR_OUT}/include"
ln -s "lib64/clang/${LLVM_RELEASE_VERSION}/include" "${SOONG_DIST}/clang-headers"

# Normalize library file names.  All library file names must match their soname.
function extract_soname () {
    local file="$1"

    case "${OS}" in
    linux)
        readelf -d "${file}" | \
            grep '(SONAME)\s*Library soname: \[.*\]$' -o | \
            sed 's/(SONAME)\s*Library soname: \[\(.*\)\]$/\1/g'
        ;;
    darwin)
        local install_path="$(otool -D "${file}" | sed -n 2p)"
        if [ -n "${install_path}" ]; then
            basename "${install_path}"
        fi
        ;;
    esac
}

for file in "${SOONG_OUT}/dist/lib"*"/"*; do
    soname="$(extract_soname "${file}")"
    if [ -n "${soname}" -a "$(basename "${file}")" != "${soname}" ]; then
        mv "${file}" "$(dirname "${file}")/${soname}"
    fi
done

# Package binaries and shared libs
(
    cd "${SOONG_OUT}/dist"
    zip -qryX build-prebuilts.zip *
)

if [ -n "${DIST_DIR}" ]; then
    mkdir -p "${DIST_DIR}" || true
    cp "${SOONG_OUT}/dist/build-prebuilts.zip" "${DIST_DIR}/"
fi
