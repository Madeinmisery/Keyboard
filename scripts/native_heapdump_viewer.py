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

"""Generates a human-interpretable view of a native heap dump from 'am dumpheap -n'."""

import os
import os.path
import re
import subprocess
import sys
import zipfile
import logging

class Args:
  _usage = """
Usage:
1. Collect a native heap dump from the device. For example:
   $ adb shell stop
   $ adb shell setprop libc.debug.malloc.program app_process
   $ adb shell setprop libc.debug.malloc.options backtrace=64
   $ adb shell start
    (launch and use app)
   $ adb shell am dumpheap -n <pid> /data/local/tmp/native_heap.txt
   $ adb pull /data/local/tmp/native_heap.txt

2. Run the viewer:
   $ python native_heapdump_viewer.py [options] native_heap.txt
      [--verbose]: verbose output
      [--html]: interactive html output
      [--reverse]: reverse the backtraces (start the tree from the leaves)
      [--symbols SYMBOL_DIR] SYMBOL_DIR is the directory containing the .so files with symbols.
                 Defaults to $ANDROID_PRODUCT_OUT/symbols
      [--app-symbols SYMBOL_DIR] SYMBOL_DIR is the directory containing the app APK and so files.
                 Defaults to the current directory.
   This outputs a file with lines of the form:

      5831776  29.09% 100.00%    10532     71b07bc0b0 /system/lib64/libandroid_runtime.so Typeface_createFromArray frameworks/base/core/jni/android/graphics/Typeface.cpp:68

   5831776 is the total number of bytes allocated at this stack frame, which
   is 29.09% of the total number of bytes allocated and 100.00% of the parent
   frame's bytes allocated. 10532 is the total number of allocations at this
   stack frame. 71b07bc0b0 is the address of the stack frame.
"""

  def __init__(self):
    self.verbose = False
    self.html_output = False
    self.reverse_frames = False
    product_out = os.getenv("ANDROID_PRODUCT_OUT")
    if product_out:
      self.symboldir = product_out + "/symbols"
    else:
      self.symboldir = "./symbols"
    self.app_symboldir = ""

    i = 1
    extra_args = []
    while i < len(sys.argv):
      if sys.argv[i] == "--symbols":
        i += 1
        self.symboldir = sys.argv[i] + "/"
      elif sys.argv[i] == "--app-symbols":
        i += 1
        self.app_symboldir = sys.argv[i] + "/"
      elif sys.argv[i] == "--verbose":
        self.verbose = True
      elif sys.argv[i] == "--html":
        self.html_output = True
      elif sys.argv[i] == "--reverse":
        self.reverse_frames = True
      elif sys.argv[i][0] == '-':
        print "Invalid option " + sys.argv[i]
      else:
        extra_args.append(sys.argv[i])
      i += 1

    if len(extra_args) != 1:
      print self._usage
      sys.exit(1)

    self.native_heap = extra_args[0]

class Backtrace:
  def __init__(self, is_zygote, size, num_allocs, frames):
    self.is_zygote = is_zygote
    self.size = size
    self.num_allocs = num_allocs
    self.frames = frames

class Mapping:
  def __init__(self, start, end, offset, name):
    self.start = start
    self.end = end
    self.offset = offset
    self.name = name

class FrameDescription:
  def __init__(self, function, location, library):
    self.function = function
    self.location = location
    self.library = library

def GetVersion(native_heap):
  """Get the version of the native heap dump."""

  re_line = re.compile("Android\s+Native\s+Heap\s+Dump\s+(?P<version>v\d+\.\d+)\s*$")
  matched = 0
  for line in open(native_heap, "r"):
    m = re_line.match(line)
    if m:
      return m.group('version')
  return None

def GetNumFieldValidByParsingLines(native_heap):
  """Determine if the num field is valid by parsing the backtrace lines.

  Malloc debug for N incorrectly set the num field to the number of
  backtraces instead of the number of allocations with the same size and
  backtrace. Read the file and if at least three lines all have the field
  set to the number of backtraces values, then consider this generated by
  the buggy malloc debug and indicate the num field is not valid.

  Returns:
    True if the num field is valid.
    False if the num field is not valid and should be ignored.
  """

  re_backtrace = re.compile("Backtrace\s+size:\s+(?P<backtrace_size>\d+)")

  re_line = re.compile("z\s+(?P<zygote>\d+)\s+sz\s+(?P<size>\d+)\s+num\s+(?P<num_allocations>\d+)")
  matched = 0
  backtrace_size = 0
  for line in open(native_heap, "r"):
    if backtrace_size == 0:
      m = re_backtrace.match(line)
      if m:
        backtrace_size = int(m.group('backtrace_size'))
    parts = line.split()
    if len(parts) > 7 and parts[0] == "z" and parts[2] == "sz":
      m = re_line.match(line)
      if m:
        num_allocations = int(m.group('num_allocations'))
        if num_allocations == backtrace_size:
          # At least three lines must match this pattern before
          # considering this the old buggy version of malloc debug.
          matched += 1
          if matched == 3:
            return False
        else:
          return True
  return matched == 0

def GetNumFieldValid(native_heap):
  version = GetVersion(native_heap)
  if not version or version == "v1.0":
    # Version v1.0 was produced by a buggy version of malloc debug where the
    # num field was set incorrectly.
    # Unfortunately, Android P produced a v1.0 version that does set the
    # num field. Do one more check to see if this is the broken version.
    return GetNumFieldValidByParsingLines(native_heap)
  else:
    return True

def GetMappingFromOffset(mapping, app_symboldir):
  """
  If the input mapping is a zip file, translate the contained uncompressed files and add mapping
  entries.

  This is done to handle symbols for the uncompressed .so files inside APKs. With the replaced
  mappings, the script looks up the .so files as separate files.
  """
  basename = os.path.basename(mapping.name)
  zip_name = app_symboldir + basename
  if os.path.isfile(zip_name):
    opened_zip = zipfile.ZipFile(zip_name)
    if opened_zip:
      # For all files in the zip, add mappings for the internal files.
      for file_info in opened_zip.infolist():
        # Only add stored files since it doesn't make sense to have PC into compressed ones.
        if file_info.compress_type == zipfile.ZIP_STORED:
          zip_header_entry_size = 30
          data_offset = (file_info.header_offset
              + zip_header_entry_size
              + len(file_info.filename)
              + len(file_info.extra)
              + len(file_info.comment))
          end_offset = data_offset + file_info.file_size
          if mapping.offset >= data_offset and mapping.offset < end_offset:
            # Round up the data_offset to the nearest page since the .so must be aligned.
            so_file_alignment = 4096
            data_offset += so_file_alignment - 1;
            data_offset -= data_offset % so_file_alignment;
            mapping.name = file_info.filename
            mapping.offset -= data_offset
            break
  return mapping

def ParseNativeHeap(native_heap, reverse_frames, num_field_valid, app_symboldir):
  """Parse the native heap into backtraces, maps.

  Returns two lists, the first is a list of all of the backtraces, the
  second is the sorted list of maps.
  """

  backtraces = []
  mappings = []

  re_map = re.compile("(?P<start>[0-9a-f]+)-(?P<end>[0-9a-f]+) .... (?P<offset>[0-9a-f]+) [0-9a-f]+:[0-9a-f]+ [0-9]+ +(?P<name>.*)")

  for line in open(native_heap, "r"):
    # Format of line:
    #   z 0  sz       50  num    1  bt 000000000000a100 000000000000b200
    parts = line.split()
    if len(parts) > 7 and parts[0] == "z" and parts[2] == "sz":
      is_zygote = parts[1] != "1"
      size = int(parts[3])
      if num_field_valid:
        num_allocs = int(parts[5])
      else:
        num_allocs = 1
      frames = map(lambda x: int(x, 16), parts[7:])
      if reverse_frames:
        frames = list(reversed(frames))
      backtraces.append(Backtrace(is_zygote, size, num_allocs, frames))
    else:
      # Parse map line:
      #   720de01000-720ded7000 r-xp 00000000 fd:00 495  /system/lib64/libc.so
      m = re_map.match(line)
      if m:
        # Offset of mapping start
        start = int(m.group('start'), 16)
        # Offset of mapping end
        end = int(m.group('end'), 16)
        # Offset within file that is mapped
        offset = int(m.group('offset'), 16)
        name = m.group('name')
        mappings.append(GetMappingFromOffset(Mapping(start, end, offset, name), app_symboldir))
  return backtraces, mappings

def FindMapping(mappings, addr):
  """Find the mapping given addr.

  Returns the mapping that contains addr.
  Returns None if there is no such mapping.
  """

  min = 0
  max = len(mappings) - 1
  while True:
    if max < min:
      return None
    mid = (min + max) // 2
    if mappings[mid].end <= addr:
      min = mid + 1
    elif mappings[mid].start > addr:
      max = mid - 1
    else:
      return mappings[mid]


def ResolveAddrs(html_output, symboldir, app_symboldir, backtraces, mappings):
  """Resolve address libraries and offsets.

  addr_offsets maps addr to .so file offset
  addrs_by_lib maps library to list of addrs from that library
  Resolved addrs maps addr to FrameDescription

  Returns the resolved_addrs hash.
  """

  addr_offsets = {}
  addrs_by_lib = {}
  resolved_addrs = {}
  empty_frame_description = FrameDescription("???", "???", "???")
  for backtrace in backtraces:
    for addr in backtrace.frames:
      if addr in addr_offsets:
        continue
      mapping = FindMapping(mappings, addr)
      if mapping:
        addr_offsets[addr] = addr - mapping.start + mapping.offset
        if not (mapping.name in addrs_by_lib):
          addrs_by_lib[mapping.name] = []
        addrs_by_lib[mapping.name].append(addr)
      else:
        resolved_addrs[addr] = empty_frame_description

  # Resolve functions and line numbers.
  if html_output == False:
    print "Resolving symbols using directory %s..." % symboldir

  for lib in addrs_by_lib:
    sofile = app_symboldir + lib
    if not os.path.isfile(sofile):
      sofile = symboldir + lib
    if os.path.isfile(sofile):
      file_offset = 0
      result = subprocess.check_output(["objdump", "-w", "-j", ".text", "-h", sofile])
      for line in result.split("\n"):
        splitted = line.split()
        if len(splitted) > 5 and splitted[1] == ".text":
          file_offset = int(splitted[5], 16)
          break

      input_addrs = ""
      for addr in addrs_by_lib[lib]:
        input_addrs += "%s\n" % hex(addr_offsets[addr] - file_offset)

      p = subprocess.Popen(["addr2line", "-C", "-j", ".text", "-e", sofile, "-f"], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
      result = p.communicate(input_addrs)[0]
      addr2line_rc = p.returncode
      if addr2line_rc and (addr2line_rc < 0):
        logging.warn("addr2line on " + sofile + " terminated by signal " + str(-1 * addr2line_rc))
      splitted = result.split("\n")
      for x in range(0, len(addrs_by_lib[lib])):
        try:
          function = splitted[2*x];
          location = splitted[2*x+1];
          resolved_addrs[addrs_by_lib[lib][x]] = FrameDescription(function, location, lib)
        except Exception:
          logging.warn("exception while resolving symbols", exc_info=True)
          resolved_addrs[addrs_by_lib[lib][x]] = FrameDescription("---", "---", lib)
    else:
      if html_output == False:
        print "%s not found for symbol resolution" % lib

      fd = FrameDescription("???", "???", lib)
      for addr in addrs_by_lib[lib]:
        resolved_addrs[addr] = fd

  return resolved_addrs

def Addr2Line(resolved_addrs, addr):
  if addr == "ZYGOTE" or addr == "APP":
    return FrameDescription("", "", "")

  return resolved_addrs[int(addr, 16)]

class AddrInfo:
  def __init__(self, addr):
    self.addr = addr
    self.size = 0
    self.number = 0
    self.num_allocs = 0
    self.children = {}

  def addStack(self, size, num_allocs, stack):
    self.size += size * num_allocs
    self.number += num_allocs
    if len(stack) > 0:
      child = stack[0]
      if not (child.addr in self.children):
        self.children[child.addr] = child
      self.children[child.addr].addStack(size, num_allocs, stack[1:])

def Display(resolved_addrs, indent, total, parent_total, node):
  fd = Addr2Line(resolved_addrs, node.addr)
  total_percent = 0
  if total != 0:
    total_percent = 100 * node.size / float(total)
  parent_percent = 0
  if parent_total != 0:
    parent_percent = 100 * node.size / float(parent_total)
  print "%9d %6.2f%% %6.2f%% %8d %s%s %s %s %s" % (node.size, total_percent, parent_percent, node.number, indent, node.addr, fd.library, fd.function, fd.location)
  children = sorted(node.children.values(), key=lambda x: x.size, reverse=True)
  for child in children:
    Display(resolved_addrs, indent + "  ", total, node.size, child)

def DisplayHtml(verbose, resolved_addrs, total, node, extra, label_count):
  fd = Addr2Line(resolved_addrs, node.addr)
  if verbose:
    lib = fd.library
  else:
    lib = os.path.basename(fd.library)
  total_percent = 0
  if total != 0:
    total_percent = 100 * node.size / float(total)
  label = "%d %6.2f%% %6d %s%s %s %s" % (node.size, total_percent, node.number, extra, lib, fd.function, fd.location)
  label = label.replace("&", "&amp;")
  label = label.replace("'", "&apos;")
  label = label.replace('"', "&quot;")
  label = label.replace("<", "&lt;")
  label = label.replace(">", "&gt;")
  children = sorted(node.children.values(), key=lambda x: x.size, reverse=True)
  print '<li>'
  if len(children) > 0:
    print '<label for="' + str(label_count) + '">' + label + '</label>'
    print '<input type="checkbox" id="' + str(label_count) + '"/>'
    print '<ol>'
    label_count += 1
    for child in children:
      label_count = DisplayHtml(verbose, resolved_addrs, total, child, "", label_count)
    print '</ol>'
  else:
    print label
  print '</li>'

  return label_count

def CreateHtml(verbose, app, zygote, resolved_addrs):
  print """
<!DOCTYPE html>
<html><head><style>
li input {
    display: none;
}
li input:checked + ol > li {
    display: block;
}
li input + ol > li {
    display: none;
}
li {
    font-family: Roboto Mono,monospace;
}
label {
    font-family: Roboto Mono,monospace;
    cursor: pointer
}
</style></head><body>Native allocation HTML viewer<br><br>
Click on an individual line to expand/collapse to see the details of the
allocation data<ol>
"""

  label_count = 0
  label_count = DisplayHtml(verbose, resolved_addrs, app.size, app, "app ", label_count)
  if zygote.size > 0:
    DisplayHtml(verbose, resolved_addrs, zygote.size, zygote, "zygote ", label_count)
  print "</ol></body></html>"

def main():
  args = Args()

  num_field_valid = GetNumFieldValid(args.native_heap)

  backtraces, mappings = ParseNativeHeap(args.native_heap, args.reverse_frames, num_field_valid,
      args.app_symboldir)
  # Resolve functions and line numbers
  resolved_addrs = ResolveAddrs(args.html_output, args.symboldir, args.app_symboldir, backtraces,
      mappings)

  app = AddrInfo("APP")
  zygote = AddrInfo("ZYGOTE")

  for backtrace in backtraces:
    stack = []
    for addr in backtrace.frames:
      stack.append(AddrInfo("%x" % addr))
    stack.reverse()
    if backtrace.is_zygote:
      zygote.addStack(backtrace.size, backtrace.num_allocs, stack)
    else:
      app.addStack(backtrace.size, backtrace.num_allocs, stack)

  if args.html_output:
    CreateHtml(args.verbose, app, zygote, resolved_addrs)
  else:
    print ""
    print "%9s %6s %6s %8s    %s %s %s %s" % ("BYTES", "%TOTAL", "%PARENT", "COUNT", "ADDR", "LIBRARY", "FUNCTION", "LOCATION")
    Display(resolved_addrs, "", app.size, app.size + zygote.size, app)
    print ""
    Display(resolved_addrs, "", zygote.size, app.size + zygote.size, zygote)
    print ""

if __name__ == '__main__':
  main()
