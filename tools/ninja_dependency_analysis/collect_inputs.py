#!/usr/bin/env python3

# Copyright 2022, The Android Open Source Project
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import argparse
import json
import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from operator import itemgetter


def build_cmd(ninja_binary, ninja_file, target, exempted_file_list):
    cmd = [ninja_binary, "-f", ninja_file, "-t", "inputs"]
    if exempted_file_list is not None and exempted_file_list.exists():
        with open(exempted_file_list) as fin:
            for l in map(str.strip, fin.readlines()):
                if len(l) > 0:
                    cmd.extend(['-e', l])
    cmd.append(target)

    return cmd


def count_project(projects, input_files):
    project_count = dict()
    for p in projects:
        file_count = sum(f.startswith(p + os.path.sep) for f in input_files)
        if file_count > 0:
            project_count[p] = file_count

    return OrderedDict(
        sorted(project_count.items(), key=itemgetter(1), reverse=True))


parser = argparse.ArgumentParser()

parser.add_argument('-n', '--ninja_binary', type=pathlib.Path, required=True)
parser.add_argument('-f', '--ninja_file', type=pathlib.Path, required=True)
parser.add_argument('-t', '--target', type=str, required=True)
parser.add_argument('-e', '--exempted_file_list', type=pathlib.Path)
group = parser.add_mutually_exclusive_group()
group.add_argument('-r', '--repo_project_list', type=pathlib.Path)
group.add_argument('-m', '--repo_manifest', type=pathlib.Path)
args = parser.parse_args()

input_files = sorted(
    subprocess.check_output(
        build_cmd(args.ninja_binary, args.ninja_file, args.target,
                  args.exempted_file_list)).decode(
                      sys.stdout.encoding).strip().split("\n"))

result = dict()
result["input_files"] = input_files

if args.repo_project_list is not None and args.repo_project_list.exists():
    with open(args.repo_project_list) as fin:
        projects = list(map(str.strip, fin.readlines()))
elif args.repo_manifest is not None and args.repo_manifest.exists():
    projects = [
        p.attrib["path"]
        for p in ET.parse(args.repo_manifest).getroot().findall("project")
    ]

if projects is not None:
    project_to_count = count_project(projects, input_files)
    result["project_count"] = project_to_count
    result["total_project_count"] = len(project_to_count)

result["total_input_count"] = len(input_files)
print(json.dumps(result, indent=2))
