#!/bin/bash

# Copyright (C) 2021 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Usage:
#   development/gki/kmi_abi_chk/kmi_static_chk.sh \
#     <current_symbol_info> <previous_symbol_info>
#

tmpfile=$(mktemp /tmp/linux-symvers.XXXXXX)

# Filter for vmlinux EXPORTE_SYMBOL* and remove trailing white spaces.
grep "vmlinux.EXPORT_SYMBOL" $1 | sed 's/[ \t]*$//' > $tmpfile

echo "Current kernel symbol file, $1, is checking aginst:"
# if nothing is found, grep returns 1, which means every symbol in the
# previous release (usually in *.symvers-$BID) can be found in the current
# release, so is considered successful here.
ret=0
for f in $2-*; do
  echo "	$f"
  grep -vf $tmpfile $f > /dev/null
  if [ $? -eq 0 ]; then
    ret=1
    echo "$f contains symbol(s) not found in, or incompatible with, $1." >&2
  fi
done

rm $tmpfile
exit $ret
