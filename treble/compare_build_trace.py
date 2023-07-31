#!/usr/bin/env python3
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

import sys

from read_build_trace_gz import Trace

def compare(target, target_name, ref, ref_name, ignore_text=None):
    additional_mod = dict()
    duration_sum = 0
    for mod in target.duration:
        if ignore_text and ignore_text in mod:
            continue
        if mod.replace(target_name, ref_name) not in ref.duration:
            additional_mod[mod] = target.duration[mod]
            duration_sum += target.duration[mod]

    return sorted(additional_mod.items(), key=lambda x:x[1], reverse=True), duration_sum

def main(argv):
    # target_build.trace.gz target_name ref_build.trace.gz ref_name (ignore_text)
    ignore_text = None
    if len(argv) == 6:
        ignore_text = argv[5]
    elif len(argv) < 5 or len(argv) > 6:
        print("usage: compare_build_trace.py target_build.trace.gz target_name ref_build.trace.gz ref_name (ignore_text)")
        sys.exit(1)

    additional_modules, additional_time = compare(Trace(argv[1]), argv[2], Trace(argv[3]), argv[4], ignore_text)
    for item in additional_modules:
        print('{min}m {sec}s {msec}ms: {name}'.format(
            min = item[1] // 60000000,
            sec = item[1] % 60000000 // 1000000,
            msec = item[1] % 1000000 // 1000,
            name = item[0]
        ))
    print('Total: {min}m {sec}s {msec}ms'.format(
        min = additional_time // 60000000,
        sec = additional_time % 60000000 // 1000000,
        msec = additional_time % 1000000 // 1000
    ))

if __name__ == '__main__':
    main(sys.argv)
