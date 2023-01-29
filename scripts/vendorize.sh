#!/bin/bash
#
# Copyright (C) 2023 The Android Open Source Project
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

# Usage: Run this script to vendorized crates in external/rust/crates
#
# Copies generated .cargo-checksum.json files into existing crates in
# external/rust/crates.
#
# 0. repo branch --all vendorize
#
# 1. Create a temporary crate with versioned dependencies
#    for each of the crates external/rust/crates
#
# 2. Create a .cargo/config.toml that redirects cargo to the
#    external/rust/crates instead of crates.io
#
# 3. Runs "cargo vendor --offline" to create a vendor directory
#    with .cargo-checksum.json files. Handles any source changes
#    in those crates due to step #2.
#
# 4. Copies .cargo-checksum.json to each external/rust/crates

# Step 1 - create temporary crate referencing all external crates

function cleanup {      
#  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
}

trap cleanup EXIT

WORK_DIR=`mktemp -d`
SCRIPT_DIR="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# Script is ROOT/development/scripts
CRATES="$(dirname $(dirname $SCRIPT_DIR))/external/rust/crates"

cd $CRATES
dependencies="[dependencies]"
for cargo in */Cargo.toml
do
    version=`sed -n 's/^version = \"\([^"]*\)"/\1/p' $cargo | head -1`
    name=`sed -n 's/^name = \"\([^"]*\)"/\1/p' $cargo | head -1`
    # These crates have problems, skip them
    if [[ $name == "libsqlite3-sys" || $name == "remove_dir_all" ]]; then
       continue;
    fi
    dependency="$name = {version = \"$version\"}"
    dependencies=$dependencies$'\n'$dependency
done

cd $WORK_DIR
cat <<EOF > Cargo.toml
[package]
edition = "2018"
name = "vendorize"
version = "1.0.0"

$dependencies
EOF

mkdir src
cat <<EOF > src/main.rs
fn main() {}
EOF

# Step 2

mkdir .cargo
cat <<EOF > .cargo/config.toml
[source.android-crates]
directory = "${CRATES}"

[source.crates-io]
replace-with = "android-crates"
EOF

# Step 3

cargo vendor --offline

# Step 4 - copy .cargo-checksum.json files

cd vendor
for crate in *
do
    cp ${crate}/.cargo-checksum.json ${CRATES}/${crate}
done

echo Done
