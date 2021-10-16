#!/usr/bin/env python3
#
# Copyright (C) 2022 The Android Open Source Project
#
"""A script to parse/analyze/show data in a ninja.log file."""

import argparse
import io
import os
import re
import sys
from typing import List, Tuple

# Please keep everything as simple as possible.
# Read from stdin or a file, accept a few flags, and dump to stdout.
# A job's (end_time - start_time) is its "run time".
# If a job runs in parallel with K other jobs, its "cost" is "run time"/(K+1).
# A group with high run-time uses a lot of CPU resource,
# but a group with high "cost" is the real bottleneck.
SCRIPT_NAME = os.path.basename(__file__)
N_SOME_DATA = 10  # dump first/last 10 data records to debug
N_TOP_GROUPS = 30  # number of top groups to dump
N_TOP_JOBS = 300  # number of top jobs to dump
LONG_JOB_SECS = 20  # skip jobs used less than 20 seconds in the top list
COSTLY_JOB_SECS = 0.5  # skip jobs cost less than 0.5 second in the top list
HUGE_RUN_SECS = 600  # report jobs running for more than 600 seconds
LONG_RUN_MSECS = 60000  # jobs run > 60 seconds are in the LONG(...) groups
OTHER_COSTLY_SECS = 30  # jobs cost 30 seconds or more are reported
OTHER_COSTLY_USED_SECS = 300  # jobs used 300 seconds or more are reported
SECONDS_PER_PERIOD = 10  # divide build time into 10-second periods


def parse_args():
  """Parse main arguments."""
  parser = argparse.ArgumentParser(SCRIPT_NAME)
  def add_flag(name: str, text: str):
    parser.add_argument("--" + name, action="store_true",
                        default=False, help=text)
  add_flag("some_data", "dump some data read from ninja_log file, to debug")
  add_flag("all_data", "dump all raw data read from ninja_log file, to debug")
  add_flag("groups", "dump all raw data with group names, to debug")
  add_flag("group_stats", "dump stats by group")
  add_flag("longest_jobs", "dump the longest running jobs")
  add_flag("concurrency",
           "dump maximal concurrency in %d-second periods" % SECONDS_PER_PERIOD)
  add_flag("costly_jobs",
           ("dump top %d costly jobs and jobs cost >= %d secs" +
            " or used >= %d secs") %
           (OTHER_COSTLY_SECS, OTHER_COSTLY_USED_SECS, N_TOP_JOBS))
  add_flag("costly_groups",
           ("dump top %d groups by total and average cost.") % N_TOP_GROUPS)
  # Call this script with --log path_to_ninja_log, or let it read from stdin.
  parser.add_argument("--log", help="path to .ninja_log file")
  return parser.parse_args()


def dump_header(title: str):
  """Dump section header before the section data."""
  sharp_line = "#" * (len(title) + 8)
  print("\n" + sharp_line)
  print("###", title, "###")
  print(sharp_line)


# Input stdin should be standard .ninja.log file format:
#     1st line: "# ninja log v5"
#  other lines: start_msec end_msec hash_str out_file_path command_hash
# A command can generate multiple output files, so multiple consecutive lines
# could have the same start_msec, end_msec, and command_hash.
# All jobs belonging to the same command job are stored into a data record,
# all records are in a data list:
#  data[k] = (start_msec, end_msec, [out_file_path])
#            of the k'th ended job in ninja.log.
DataRecord = Tuple[int, int, List[str]]
DataRecordWithGroup = Tuple[int, int, List[str], str]
DataList = List[DataRecord]
DataListWithGroup = List[DataRecordWithGroup]
EventList = List[Tuple[int, str, int]]


def read_data(inf) -> DataList:
  """Read from stdin, return a data list."""
  data = []
  line = inf.readline()
  if line != "# ninja log v5\n":
    print("ERROR: 1st line should be \'# ninja log v5', but got: ", line)
    return []
  # Remember previous line's (start_msec, end_msec, command_hash).
  prev_line_data = (0, 0, "")
  # Output files should have different command hashes, except continuous lines
  # of output files from the same command.
  all_command_hashes = set()
  num_lines = 1  # number of lines read so far
  first_data_line = 2
  # A ninja_log file can contain large number of older runs,
  # and create many "Found smaller end_msec" messages.
  # Keep a counter of such cases and output only the last one.
  num_resets = 0  # number of times a smaller end_msec was found
  while True:
    line = inf.readline()
    if not line:
      break
    num_lines += 1
    values = line.split("\t")
    (start_time, end_time, _, file_name, command_hash) = values
    start_time = int(start_time)
    end_time = int(end_time)
    # command_hash has EOL, but that's okay for our comparisons
    # basic checks:
    if end_time < start_time:
      print("ERROR: start_time > end_time:", line)
      exit(1)
    if end_time == start_time:
      print("WARNING: start_time == end_time:", line)
    # (1) If the end_time < previous line's, this is a new ninja run.
    if end_time < prev_line_data[1]:
      # reset data list
      num_resets += 1
      last_reset_line = (num_lines, start_time, end_time,
                         prev_line_data[0], prev_line_data[1])
      data = []
      all_command_hashes = set()
      first_data_line = num_lines
    # (2) A command hash should be a new one or equal to previous line's.
    if command_hash != prev_line_data[2]:  # normal case
      if command_hash in all_command_hashes:
        print("# ERROR: repeated command hash at line %d: %s" %
              (num_lines, line))
        exit(1)
      all_command_hashes.add(command_hash)
      prev_line_data = (start_time, end_time, command_hash)
      data.append((start_time, end_time, [file_name]))
    else:  # (3) same command_hash, should have the same start and end times.
      # All such same-command-hash lines are combined into one record.
      if start_time != prev_line_data[0] or end_time != prev_line_data[1]:
        print("# ERROR: same command hash at line %d: %s" % (num_lines, line))
        exit(1)
      if command_hash not in all_command_hashes:
        print("# ERROR: missing command hash in collected set, line %d: %s" %
              (num_lines, line))
        exit(1)
      # append to previous data entry, for the same command job
      data[-1][2].append(file_name)
  collected_lines = num_lines - first_data_line + 1
  if num_resets > 0:
    print("# Found", num_resets, "smaller end_msec lines.")
    print(("# The last one at line %s, start_msec=%d end_msec=%d\n" +
           "# Its previous line: start_msec=%d end_msec=%d") % last_reset_line)
  print("# Collected %d commands in %d lines, line %d to line %d" %
        (len(data), collected_lines, first_data_line, num_lines))
  return data


def dump_one_record(idx: int, record: DataRecord):
  """Print data[idx] in one line per output file."""
  (start, end, files) = record
  print("data[%d]: %.3f %.3f %s" % (idx, start / 1000, end / 1000, files[0]))
  if len(files) > 1:
    indent = " " * len("data[%d]" % idx)
    for i in range(1, len(files)):
      print(indent + ":", files[i])


def dump_n_records(data: DataList, first_last: str, idx0: int, num: int):
  dump_header("Dump %s %d data records to debug" % (first_last, num))
  print("# data[idx]: start_sec end_sec out_file_name")
  print("#          : other_out_file_from_the_same_command")
  for i in range(idx0, idx0 + num):
    dump_one_record(i, data[i])


def dump_groups(data: DataListWithGroup):
  """Only all data with group name to debug."""
  dump_header("Dump all data with group name to debug")
  print("# data[idx]: group_name out_file_name")
  print("#          : group_name other_out_file_from_the_same_command")
  for idx, record in enumerate(data):
    (_, _, files, group) = record
    print("data[%d]: %s %s" % (idx, group, files[0]))
    if len(files) > 1:
      indent = " " * len("data[%d]" % idx)
      for i in range(1, len(files)):
        print(indent + ":", group, files[i])


def dump_group(data: DataListWithGroup, group_name: str):
  """Dump all files in the given group_name."""
  dump_header("Dump files in the '" + group_name + "' group")
  output_lines = []
  for (start, end, files, group) in data:
    if group == group_name:
      for name in files:
        output_lines.append(
            "%9.3f %9.3f %9.3f %s" %
            ((end - start) / 1000, start / 1000, end / 1000, name))
  if output_lines:
    print("used_secs start_sec   end_sec file_name")
    for line in output_lines:
      print(line)
  else:
    print("# found no file in the '%s' group" % group_name)


def sort_and_dump(count_list, total_secs, title, key_num, top_n):
  """Sort count_list by key_num and dump top_n records."""
  dump_header(title)
  print("# (skip groups with fewer than 10 commands and 10 seconds/command)")
  print("#commands secs percent avg_secs group_name")
  count_list.sort(reverse=True, key=lambda x: x[key_num])
  line = 0
  for (num, secs, avg_msecs, group) in count_list:
    line += 1
    if line > top_n:
      break
    if num < 10 and avg_msecs < 10000:
      continue  # no need to debug rare cases unless they are slow
    print("%6d %7d %6.2f%% %8.3f %s" %
          (num, secs, secs * 100 / total_secs, avg_msecs / 1000, group))


def dump_group_stats(data: DataListWithGroup):
  """Dump stats for each file group."""
  dump_header("Dump stats per file group")
  count = {}  # group -> number of files in the group
  used_time = {}  # group -> total used time in msecs
  total_count = 0
  total_used_msecs = 0
  for (start_msec, end_msec, _, group) in data:
    total_count += 1
    used_msecs = end_msec - start_msec
    total_used_msecs += used_msecs
    if group in count:
      count[group] += 1
      used_time[group] += used_msecs
    else:
      count[group] = 1
      used_time[group] = used_msecs
  print("# Total command count =", total_count)
  print("# Total real time seconds = %.3f" % (total_used_msecs / 1000))
  count_list = [(count[group], int(used_time[group] / 1000),
                 int(used_time[group] / count[group]), group)
                for group in count]
  total_secs = max(total_used_msecs / 1000, 1)
  sort_and_dump(count_list, total_secs,
                "Most popular command groups.", 0, 999)  # dump all groups
  def sort_dump_top_groups(kind, idx):
    header = "Top %d groups by %s used seconds." % (N_TOP_GROUPS, kind)
    sort_and_dump(count_list, total_secs, header, idx, N_TOP_GROUPS)
  sort_dump_top_groups("total", 1)
  sort_dump_top_groups("average", 2)


# Precomputed bar strings to save time in build_x_bar and dump_concurrency.
# Although Roman numeral symbols I/X/C/M are used,
# the "bar strings" are not a Roman number.
# Each I/X/C/M represent 1/10/100/1000 jobs in dump_concurrency.
# A trailing "+" is added if some amount is larger than the current
# level symbol but less than the next level symbol.
# For n = 0..10, use 0..10 "I" characters.
BAR_I_MARKS = ["".join(["I"] * n) for n in range(11)]
BAR_I_MARKS[0] = "."
# For n = 11..100, use 0..9 "X" characters.
BAR_X_MARKS = ["".join(["X"] * n) for n in range(10)]
BAR_X_MARKS[0] = "+"
# For n = 101..1000, use 0..9 "C" characters.
BAR_C_MARKS = ["".join(["C"] * n) for n in range(10)]
BAR_C_MARKS[0] = "+"
# For n = 1001..10000, use 0..9 "M" characters.
BAR_M_MARKS = ["".join(["M"] * n) for n in range(10)]
BAR_M_MARKS[0] = "+"


def build_x_bar(num: int) -> str:
  """Return a string of III...XX... to show the scale of num."""
  # ninja could fork hundred of jobs; don't print a very long bar
  if num <= 10:
    return BAR_I_MARKS[num]
  if num <= 100:
    return BAR_I_MARKS[10] + BAR_X_MARKS[int((num - 10) / 10)]
  if num <= 1000:
    return BAR_I_MARKS[10] + BAR_X_MARKS[9] + BAR_C_MARKS[int(
        (num - 100) / 100)]
  return (BAR_I_MARKS[10] + BAR_X_MARKS[9] + BAR_C_MARKS[9] +
          BAR_M_MARKS[min(10000, int((num - 1000) / 1000))])


def create_events(data: DataListWithGroup) -> EventList:
  """Create a list of events of tuple (msec, s_or_e, job_idx)."""
  # s_or_e is 's' for start-of-a-job, 'e' for end-of-a-job.
  # When sorted, at the same msec, 'e' is before 's',
  # so we can easily remove a job before add another job.
  events = []
  for i, (start_msec, end_msec, _, _) in enumerate(data):
    # In .ninja_log, a job's end-msec is not included as its run time.
    # This function returns events, with inclusive end_msec.
    # An end-of-a-job event's time is .ninja_log file's end-msec - 1.
    events.append((start_msec, "s", i))
    events.append((end_msec - 1, "e", i))
  events.sort()
  if events[0][1] != "s":
    print("ERROR: wrong first event:", events[0], data[events[0][2]])
  last_event = events[len(events) - 1]
  if last_event[1] != "e":
    print("ERROR: wrong last event:", last_event, data[last_event[2]])
  return events


def compute_jobs_in_period(data: DataListWithGroup) -> (
        EventList, List[int], List[int], List[List[int]]):
  """Create: events, cost of jobs, concurrency of periods, jobs in periods."""
  events = create_events(data)
  # every output file costs 0 msecs initially
  costs = [0] * len(data)
  jobs = set()  # all running job indices
  last_msec = 0  # last event time
  # num_jobs[k] is the maximum concurrent jobs in period k,
  # which is from time k*SECONDS_PER_PERIOD second to the next (k+1) period.
  num_jobs = []
  # keep a list of jobs that have run sometime in period k.
  jobs_in_period = []
  for (msec, s_or_e, idx) in events:
    if jobs and msec > last_msec:
      add_msecs = (msec - last_msec) / len(jobs)
      for k in jobs:
        costs[k] += add_msecs
    last_msec = msec
    period = int(msec / 10000)
    while len(num_jobs) < period + 1:
      num_jobs.append(len(jobs))
      jobs_in_period.append(list(jobs))
    if s_or_e == "s":
      jobs.add(idx)
      num_jobs[period] = max(num_jobs[period], len(jobs))
      jobs_in_period[period].append(idx)
    elif idx in jobs:
      jobs.remove(idx)
  for k in jobs:
    print("ERROR: unfinished job ", k, ": ", data[k])
  return (events, costs, num_jobs, jobs_in_period)


def dump_concurrency(data, events, num_jobs, jobs_in_period):
  """Dump concurrency statistics."""
  dump_header("Maximal number of concurrent jobs in each %d-second period" %
              SECONDS_PER_PERIOD)
  print("# Also dump long running jobs (>= %d seconds) or" % (HUGE_RUN_SECS))
  print("# jobs >= 30 seconds when concurrency is lower than 50")
  print("# start_sec  max_num_jobs (#X*10 + #C*100 jobs)")
  max_num_jobs = 0
  printed_jobs = set()
  for i, num in enumerate(num_jobs):
    max_num_jobs = max(max_num_jobs, num)
    print("%4d %4d %s" % (SECONDS_PER_PERIOD * i, num, build_x_bar(num)))
    # print huge jobs >= HUGE_RUN_SECS, or >= 30 seconds, when num < 50
    jobs_to_print = []
    for idx in jobs_in_period[i]:
      if idx not in printed_jobs:
        (start_msec, end_msec, _, group) = data[idx]
        seconds = (end_msec - start_msec) / 1000
        if seconds >= HUGE_RUN_SECS or (seconds >= 30 and num < 50):
          printed_jobs.add(idx)
          jobs_to_print.append(idx)
    # Jobs sorted by indices to the data list, which is sorted by the end-time.
    jobs_to_print.sort()
    for idx in jobs_to_print:
      (start_msec, end_msec, files, _) = data[idx]
      seconds = (end_msec - start_msec) / 1000
      print("  RUNNING: from %d + %d to %d secs, %s" %
            (start_msec / 1000, seconds, end_msec / 1000, files[0]))
  print("# Maximal number of concurrent running jobs =", max_num_jobs)
  total_seconds = (events[-1][0] - events[0][0]) / 1000
  print("# Total run time (wall time) %d seconds." % (total_seconds))

  dump_header("Low concurrency: (concurrency<=N, total_duration_seconds)")
  # Count number of periods whose num_jobs <= (max_num_jobs/10)
  num_low_concurrency = max(5, int(max_num_jobs / 10))
  low_concurrency = [0] * num_low_concurrency
  for num in num_jobs:
    for i in range(num, num_low_concurrency):
      low_concurrency[i] += 1
  for i, num in enumerate(low_concurrency):
    if num > 0:
      seconds = num * SECONDS_PER_PERIOD
      print("LOW CONCURRENCY <= %2d:  %5d seconds, %6.2f of %d" %
            (i, seconds, seconds / total_seconds, total_seconds))


def dump_costly_jobs(data: DataListWithGroup, costs):
  """Sort and dump jobs by their costs in time."""
  all_costs_jobs = [(costs[i], i) for i in range(len(costs))]
  all_costs_jobs.sort(reverse=True)
  num_top_jobs = min(len(costs), N_TOP_JOBS)
  dump_header("Dump up to %d jobs cost %.1f or more seconds." %
              (num_top_jobs, COSTLY_JOB_SECS))
  print("# start_sec  end_sec real_sec cost_sec output_file")
  for i in range(num_top_jobs):
    msec, idx = all_costs_jobs[i]
    start_msec, end_msec, files, _ = data[idx]
    if msec / 1000 >= COSTLY_JOB_SECS:
      print("%11.3f %8.3f %8.3f %8.3f %s" %
            (start_msec / 1000, end_msec / 1000,
             (end_msec - start_msec) / 1000, msec / 1000, files[0]))
  other_jobs_list = []
  for i in range(num_top_jobs, len(costs) - num_top_jobs):
    msec, idx = all_costs_jobs[i]
    (start_msec, end_msec, files, _) = data[idx]
    cost_secs = msec / 1000
    used_secs = (end_msec - start_msec) / 1000
    if used_secs >= OTHER_COSTLY_USED_SECS or cost_secs >= OTHER_COSTLY_SECS:
      other_jobs_list.append(
          "%11.3f %8.3f %8.3f %8.3f %s" %
          (start_msec / 1000, end_msec / 1000,
           used_secs, cost_secs, files[0]))
  if other_jobs_list:
    print("\n# other jobs: cost >= %d secs or used >= %d secs." %
          (OTHER_COSTLY_SECS, OTHER_COSTLY_USED_SECS))
    print("# start_sec  end_sec real_sec cost_sec output_file")
    for line in other_jobs_list:
      print(line)


def dump_costly_groups(data: DataListWithGroup, costs):
  """Dump longest groups by total/average cost seconds."""
  count = {}  # group -> number of files in the group
  cost_msecs = {}  # group -> total cost time in msecs
  total_count = 0
  total_cost = 0
  for k, (_, _, _, group) in enumerate(data):
    total_count += 1
    total_cost += costs[k]
    if group in count:
      count[group] += 1
      cost_msecs[group] += costs[k]
    else:
      count[group] = 1
      cost_msecs[group] = costs[k]
  dump_header("Cost time seconds per file group")
  print("# Total file count =", total_count)
  print("# Total cost seconds = %.3f" % (total_cost / 1000))
  cost_time_list = [(count[group], int(cost_msecs[group] / 1000),
                     int(cost_msecs[group] / count[group]), group)
                    for group in cost_msecs]
  total_cost_secs = max(total_cost / 1000, 1)
  def sort_dump_top_groups(kind, idx):
    header = "Top %d groups by %s cost seconds." % (N_TOP_GROUPS, kind)
    sort_and_dump(cost_time_list, total_cost_secs, header, idx, N_TOP_GROUPS)
  sort_dump_top_groups("total", 1)
  sort_dump_top_groups("average", 2)


# Build duration is (latest end_time) - (earliest start_time).
# Sum(group B-time) = (Build duration)
# Sum(group R-time)/(Build duration) = average threads
# Reduce largest B-time ==> reduce total build time
# Reduce largest R-time ==> reduce CPU load but not necessary build time
# B-time is called cost_msecs in this program.
def compute_dump_costs(args, data: DataListWithGroup):
  """Compute and dump costs of each job and group."""
  events, costs, num_jobs, jobs_in_period = compute_jobs_in_period(data)
  if args.concurrency:
    dump_concurrency(data, events, num_jobs, jobs_in_period)
  if args.costly_jobs:
    dump_costly_jobs(data, costs)
  if args.costly_groups:
    dump_costly_groups(data, costs)


# An output file path can match multiple group name patterns.
# So the patterns are checks sequentially and could take a lot of time.
# When there is no ambiguity, it is important to put most common
# patterns first in this list. See output of dump_group_stats.
GROUP_PATTERNS = [
    (re.compile(".*\\.o$"), "*.o"),
    (re.compile(".*\\.tidy$"), "*.tidy"),
    (re.compile(".*\\.flat$"), "*.flat"),
    (re.compile(".*\\.so$"), "*.so"),
    (re.compile(".*\\.meta_module$"), "*.meta_module"),
    (re.compile(".*\\.h$"), "*.h"),
    (re.compile(".*\\.jar[0-9]*$"), "*.jar[0-9]*"),
    (re.compile(".*/metalava/.*"), "*/metalava/*"),
    (re.compile(".*\\.b?[0-9]+$"), "*.b?[0-9]+"),
    (re.compile(".*/(extra_packages|expoted-sdk-libs|gen/timestamps)$"),
     "*/(extra_packages|expoted-sdk-libs|gen/timestamps)"),
    (re.compile(".*(-|/)timestamp$"), "(-)?timestamp"),
    (re.compile(".*/exported-sdk-libs$"), "exported-sdk-libs"),
    (re.compile(
        ".*/(has_development|java-source-lists?|proguard_options|.*_contexts|.*_pubkey|.*-config)$"
    ),
     "(has_development|java-source-lists?|proguard_options|*_contexts|.*_pubkey|.*-config)"
    ),
    (re.compile(".*(_|-)aidl(|_interfaces)$"), "*/*aidl*"),
    (re.compile(".*_(registry|version|settings|metadata|dictionary)$"),
     "*_(registry|version|settings|metadata|dictionary)"),
    (re.compile(".*/metadata_[^/]*$"), "metadata_*"),
    (re.compile(".*/export_[^/]*_flags$"), "export_*_flags"),
    (re.compile(".*/_?fs_config_[^/]*$"), "_?fs_config_*"),
    (re.compile(".*(_tests?|TargetTest)$"), "*(_tests?|TargetTest)"),
    (re.compile("^out/target/.*/EXECUTABLES/.*"), "out/target/*/EXECUTABLES/*"),
    (re.compile("^out/target/.*/bin/.*"), "out/target/*/bin/*"),
    (re.compile("^out/target/.*/[A-Za-z0-9_\\-]*$"),
     "out/target/*/(simple_name)"),
    (re.compile("^out/soong/host/.*/bin/.*"), "out/soong/host/*/bin"),
    (re.compile("^out/soong/.*/unstripped/.*"), "out/soong/*/unstripped/*"),
    (re.compile("^out/soong/\\.intermediates/.*/[a-z\\-_0-9]*$"),
     ".intermediates/*/(simple_name)"),
    (re.compile("^out/host/.*/[A-Za-z0-9_\\-]*$"), "out/host/*/(simple_name)"),
    (re.compile("^/buildbot/dist_dirs/.*$"), "buildbot/dist_dirs/*"),
]


def add_group_name(data: DataList) -> DataListWithGroup:
  """For each data tuple, append its output file group name."""

  def group_name(msecs: int, file_path: str) -> str:
    for (regex, group) in GROUP_PATTERNS:
      if regex.match(file_path):
        return group
    base_name = re.sub(".*/", "*/", file_path)
    suffix = re.sub(".*\\.", "*.", base_name)
    if suffix != base_name:
      return suffix
    if msecs > LONG_RUN_MSECS:
      return base_name  # unique long job
    return "(other)"

  def check_runtime(msecs: int, group_name: str) -> str:
    if msecs > LONG_RUN_MSECS:
      return "LONG(" + group_name + ")"  # long job in a group
    return group_name

  new_data = []
  for (start, end, files) in data:
    msecs = end - start + 1
    if len(files) == 1:
      combined_name = group_name(msecs, files[0])
    else:
      names = set()
      for file_name in files:
        names.add(group_name(msecs, file_name))
      name_list = list(names)
      name_list.sort()
      combined_name = "|".join(name_list)
    new_data.append((start, end, files, check_runtime(msecs, combined_name)))
  return new_data


def dump_longest_jobs(data: DataList):
  """Dump longest N jobs."""
  all_jobs = [(end - start, i) for (i, (start, end, files)) in enumerate(data)]
  all_jobs.sort(reverse=True)
  num_top_jobs = min(len(all_jobs), N_TOP_JOBS)
  dump_header("Dump up to %d jobs used %d or more seconds."
              % (num_top_jobs, LONG_JOB_SECS))
  print("# start_sec  end_sec used_secs output_file")
  for i in range(min(len(all_jobs), num_top_jobs)):
    msec, idx = all_jobs[i]
    start_msec, end_msec, files = data[idx]
    if msec / 1000 >= LONG_JOB_SECS:
      print("%11.3f %8.3f %9.3f %s" %
            (start_msec / 1000, end_msec / 1000, msec / 1000, files[0]))


def read_dump_data(args) -> DataList:
  """Read ninja log data and dump data to debug."""
  my_input = args.log if args.log else "stdin"
  print("###", SCRIPT_NAME, "reading data from", my_input, "...")
  if args.log:
    with io.open(args.log) as log:
      data = read_data(log)
  else:
    data = read_data(sys.stdin)
  if args.some_data:
    dump_num = min(len(data), N_SOME_DATA)
    dump_n_records(data, "fist", 0, dump_num)
    dump_n_records(data, "last", len(data) - dump_num, dump_num)
  if args.all_data:
    dump_n_records(data, "all", 0, len(data))
  if args.longest_jobs:
    dump_longest_jobs(data)
  return data


def main():
  """Read data from stdin and dump various stats or top lists."""
  args = parse_args()
  data = read_dump_data(args)
  compute_costs = args.concurrency or args.costly_jobs or args.costly_groups
  if not (args.groups or args.group_stats or compute_costs):
    return
  data = add_group_name(data)
  if args.groups:
    dump_groups(data)
    dump_group(data, "(other)")
    # Add another flag to select/dump specific groups:
    # dump_group(data, "out/soong/host/*/bin")
    # dump_group(data, "LONG(.intermediates/*/(simple_name))")
    # dump_group(data, ".intermediates/*/(simple_name)")
  if args.group_stats:
    dump_group_stats(data)
  if compute_costs:
    compute_dump_costs(args, data)


if __name__ == "__main__":
  main()
