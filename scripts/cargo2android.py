#!/usr/bin/env python
#
# Copyright (C) 2019 The Android Open Source Project
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
"""Call cargo -v, parse its output, and generate Android.bp.

Usage: Run this script in a crate workspace root directory.
The Cargo.toml file should work at least for the host platform.

(1) Without other flags, "cargo2android.py --run"
    calls cargo clean, calls cargo build -v, and generates Android.bp.
    The cargo build only generates crates for the host,
    without test crates.

(2) To build crates for both host and device in Android.bp, use the
    --device flag, for example:
    cargo2android.py --run --device

    This is equivalent to using the --cargo flag to add extra builds:
    cargo2android.py --run
      --cargo "build"
      --cargo "build --target x86_64-unknown-linux-gnu"

    On MacOS, use x86_64-apple-darwin as target triple.
    Here the host target triple is used as a fake cross compilation target.
    If the crate's Cargo.toml and environment configuration works for an
    Android target, use that target triple as the cargo build flag.

(3) To build default and test crates, for host and device, use both
    --device and --tests flags:
    cargo2android.py --run --device --tests

    This is equivalent to using the --cargo flag to add extra builds:
    cargo2android.py --run
      --cargo "build"
      --cargo "build --tests"
      --cargo "build --target x86_64-unknown-linux-gnu"
      --cargo "build --tests --target x86_64-unknown-linux-gnu"

Since Android rust builds by default treat all warnings as errors,
if there are rustc warning messages, this script will add
deny_warnings:false to the owner crate module in Android.bp.
"""

from __future__ import print_function

import argparse
import os
import os.path
import re

RENAME_MAP = {
    # This map includes all changes to the default rust library module
    # names to resolve name conflicts or avoid confusion.
    'libbacktrace': 'libbacktrace_rust',
    'libgcc': 'libgcc_rust',
    'liblog': 'liblog_rust',
    'libsync': 'libsync_rust',
    'libx86_64': 'libx86_64_rust',
}

# Header added to all generated Android.bp files.
ANDROID_BP_HEADER = '// This file is generated by cargo2android.py.\n'

CARGO_OUT = 'cargo.out'  # Name of file to keep cargo build -v output.

TARGET_TMP = 'target.tmp'  # Name of temporary output directory.

# Message to be displayed when this script is called without the --run flag.
DRY_RUN_NOTE = (
    'Dry-run: This script uses ./' + TARGET_TMP + ' for output directory,\n' +
    'runs cargo clean, runs cargo build -v, saves output to ./cargo.out,\n' +
    'and writes to Android.bp in the current and subdirectories.\n\n' +
    'To do do all of the above, use the --run flag.\n' +
    'See --help for other flags, and more usage notes in this script.\n')

# Cargo -v output of a call to rustc.
RUSTC_PAT = re.compile('^ +Running `rustc (.*)`$')

# Rustc output of file location path pattern for a warning message.
WARNING_FILE_PAT = re.compile('^ *--> ([^:]*):[0-9]+')


def altered_name(name):
  return RENAME_MAP[name] if (name in RENAME_MAP) else name


def is_build_crate_name(name):
  # We added special prefix to build script crate names.
  return name.startswith('build_script_')


def is_dependent_file_path(path):
  # Absolute or dependent '.../' paths are not main files of this crate.
  return path.startswith('/') or path.startswith('.../')


def get_module_name(crate):  # to sort crates in a list
  return crate.module_name


def pkg2crate_name(s):
  return s.replace('-', '_').replace('.', '_')


def file_base_name(path):
  return os.path.splitext(os.path.basename(path))[0]


def test_base_name(path):
  return pkg2crate_name(file_base_name(path))


def unquote(s):  # remove quotes around str
  if s and len(s) > 1 and s[0] == '"' and s[-1] == '"':
    return s[1:-1]
  return s


def escape_quotes(s):  # replace '"' with '\\"'
  return s.replace('"', '\\"')


class Crate(object):
  """Information of a Rust crate to collect/emit for an Android.bp module."""

  def __init__(self, runner, outf_name):
    # Remembered global runner and its members.
    self.runner = runner
    self.debug = runner.args.debug
    self.cargo_dir = ''  # directory of my Cargo.toml
    self.outf_name = outf_name  # path to Android.bp
    self.outf = None  # open file handle of outf_name during dump*
    # Variants/results that could be merged from multiple rustc lines.
    self.host_supported = False
    self.device_supported = False
    self.has_warning = False
    # Android module properties derived from rustc parameters.
    self.module_name = ''  # unique in Android build system
    self.module_type = ''  # rust_{binary,library,test}[_host] etc.
    self.root_pkg = ''  # parent package name of a sub/test packge, from -L
    self.srcs = list()  # main_src or merged multiple source files
    self.stem = ''  # real base name of output file
    # Kept parsed status
    self.errors = ''  # all errors found during parsing
    self.line_num = 1  # runner told input source line number
    self.line = ''  # original rustc command line parameters
    # Parameters collected from rustc command line.
    self.crate_name = ''  # follows --crate-name
    self.main_src = ''  # follows crate_name parameter, shortened
    self.crate_type = ''  # bin|lib|test (see --test flag)
    self.cfgs = list()  # follows --cfg, without feature= prefix
    self.features = list()  # follows --cfg, name in 'feature="..."'
    self.codegens = list()  # follows -C, some ignored
    self.externs = list()  # follows --extern
    self.core_externs = list()  # first part of self.externs elements
    self.static_libs = list()  # e.g.  -l static=host_cpuid
    self.shared_libs = list()  # e.g.  -l dylib=wayland-client, -l z
    self.cap_lints = ''  # follows --cap-lints
    self.emit_list = ''  # e.g., --emit=dep-info,metadata,link
    self.edition = '2015'  # rustc default, e.g., --edition=2018
    self.target = ''  # follows --target

  def write(self, s):
    # convenient way to output one line at a time with EOL.
    self.outf.write(s + '\n')

  def same_flags(self, other):
    # host_supported, device_supported, has_warning are not compared but merged
    # target is not compared, to merge different target/host modules
    # externs is not compared; only core_externs is compared
    return (not self.errors and not other.errors and
            self.edition == other.edition and
            self.cap_lints == other.cap_lints and
            self.emit_list == other.emit_list and
            self.core_externs == other.core_externs and
            self.codegens == other.codegens and
            self.features == other.features and
            self.static_libs == other.static_libs and
            self.shared_libs == other.shared_libs and self.cfgs == other.cfgs)

  def merge_host_device(self, other):
    """Returns true if attributes are the same except host/device support."""
    return (self.crate_name == other.crate_name and
            self.crate_type == other.crate_type and
            self.main_src == other.main_src and self.stem == other.stem and
            self.root_pkg == other.root_pkg and not self.skip_crate() and
            self.same_flags(other))

  def merge_test(self, other):
    """Returns true if self and other are tests of same root_pkg."""
    # Before merger, each test has its own crate_name.
    # A merged test uses its source file base name as output file name,
    # so a test is mergeable only if its base name equals to its crate name.
    return (self.crate_type == other.crate_type and
            self.crate_type == 'test' and self.root_pkg == other.root_pkg and
            not self.skip_crate() and
            other.crate_name == test_base_name(other.main_src) and
            (len(self.srcs) > 1 or
             (self.crate_name == test_base_name(self.main_src)) and
             self.host_supported == other.host_supported and
             self.device_supported == other.device_supported) and
            self.same_flags(other))

  def merge(self, other, outf_name):
    """Try to merge crate into self."""
    should_merge_host_device = self.merge_host_device(other)
    should_merge_test = False
    if not should_merge_host_device:
      should_merge_test = self.merge_test(other)
    # A for-device test crate can be merged with its for-host version,
    # or merged with a different test for the same host or device.
    # Since we run cargo once for each device or host, test crates for the
    # first device or host will be merged first. Then test crates for a
    # different device or host should be allowed to be merged into a
    # previously merged one, maybe for a different device or host.
    if should_merge_host_device or should_merge_test:
      self.runner.init_bp_file(outf_name)
      with open(outf_name, 'a') as outf:  # to write debug info
        self.outf = outf
        other.outf = outf
        self.do_merge(other, should_merge_test)
      return True
    return False

  def do_merge(self, other, should_merge_test):
    """Merge attributes of other to self."""
    if self.debug:
      self.write('\n// Before merge definition (1):')
      self.dump_debug_info()
      self.write('\n// Before merge definition (2):')
      other.dump_debug_info()
    # Merge properties of other to self.
    self.host_supported = self.host_supported or other.host_supported
    self.device_supported = self.device_supported or other.device_supported
    self.has_warning = self.has_warning or other.has_warning
    if not self.target:  # okay to keep only the first target triple
      self.target = other.target
    # decide_module_type sets up default self.stem,
    # which can be changed if self is a merged test module.
    self.decide_module_type()
    if should_merge_test:
      self.srcs.append(other.main_src)
      # use a shorter name as the merged module name.
      n1 = len(self.module_name)
      n2 = len(other.module_name)
      if n2 < n1 or (n2 == n1 and other.module_name < self.module_name):
        self.module_name = other.module_name
      self.stem = self.module_name
      # This normalized root_pkg name although might be the same
      # as other module's crate_name, it is not actually used for
      # output file name. A merged test module always have multiple
      # source files and each source file base name is used as
      # its output file name.
      self.crate_name = pkg2crate_name(self.root_pkg)
    if self.debug:
      self.write('\n// After merge definition (1):')
      self.dump_debug_info()

  def find_cargo_dir(self):
    """Deepest directory with Cargo.toml and contains the main_src."""
    if not is_dependent_file_path(self.main_src):
      dir_name = os.path.dirname(self.main_src)
      while dir_name:
        if os.path.exists(dir_name + '/Cargo.toml'):
          self.cargo_dir = dir_name
          return
        dir_name = os.path.dirname(dir_name)

  def parse(self, line_num, line):
    """Find important rustc arguments to convert to Android.bp properties."""
    self.line_num = line_num
    self.line = line
    args = line.split()  # Loop through every argument of rustc.
    i = 0
    while i < len(args):
      arg = args[i]
      if arg == '--crate-name':
        self.crate_name = args[i + 1]
        i += 2
        # shorten imported crate main source path
        self.main_src = re.sub('^/[^ ]*/registry/src/', '.../', args[i])
        self.main_src = re.sub('^.../github.com-[0-9a-f]*/', '.../',
                               self.main_src)
        self.find_cargo_dir()
        if self.cargo_dir and not self.runner.args.onefile:
          # Write to Android.bp in the subdirectory with Cargo.toml.
          self.outf_name = self.cargo_dir + '/Android.bp'
          self.main_src = self.main_src[len(self.cargo_dir) + 1:]
      elif arg == '--crate-type':
        i += 1
        if self.crate_type:
          self.errors += '  ERROR: multiple --crate-type '
          self.errors += self.crate_type + ' ' + args[i] + '\n'
          # TODO(chh): handle multiple types, e.g. lexical-core-0.4.6 has
          #   crate-type = ["lib", "staticlib", "cdylib"]
          # output: debug/liblexical_core.{a,so,rlib}
          # cargo calls rustc with multiple --crate-type flags.
          # rustc can accept:
          #   --crate-type [bin|lib|rlib|dylib|cdylib|staticlib|proc-macro]
          #   Comma separated list of types of crates for the compiler to emit
        self.crate_type = args[i]
      elif arg == '--test':
        # only --test or --crate-type should appear once
        if self.crate_type:
          self.errors += ('  ERROR: found both --test and --crate-type ' +
                          self.crate_type + '\n')
        else:
          self.crate_type = 'test'
      elif arg == '--target':
        i += 1
        self.target = args[i]
      elif arg == '--cfg':
        i += 1
        if args[i].startswith('\'feature='):
          self.features.append(unquote(args[i].replace('\'feature=', '')[:-1]))
        else:
          self.cfgs.append(args[i])
      elif arg == '--extern':
        i += 1
        extern_names = re.sub('=/[^ ]*/deps/', ' = ', args[i])
        self.externs.append(extern_names)
        self.core_externs.append(re.sub(' = .*', '', extern_names))
      elif arg == '-C':  # codegen options
        i += 1
        # ignore options not used in Android
        if not (args[i].startswith('debuginfo=') or
                args[i].startswith('extra-filename=') or
                args[i].startswith('incremental=') or
                args[i].startswith('metadata=')):
          self.codegens.append(args[i])
      elif arg == '--cap-lints':
        i += 1
        self.cap_lints = args[i]
      elif arg == '-L':
        i += 1
        if args[i].startswith('dependency=') and args[i].endswith('/deps'):
          if '/' + TARGET_TMP + '/' in args[i]:
            self.root_pkg = re.sub(
                '^.*/', '', re.sub('/' + TARGET_TMP + '/.*/deps$', '', args[i]))
          else:
            self.root_pkg = re.sub('^.*/', '',
                                   re.sub('/[^/]+/[^/]+/deps$', '', args[i]))
      elif arg == '-l':
        i += 1
        if args[i].startswith('static='):
          self.static_libs.append(re.sub('static=', '', args[i]))
        elif args[i].startswith('dylib='):
          self.shared_libs.append(re.sub('dylib=', '', args[i]))
        else:
          self.shared_libs.append(args[i])
      elif arg == '--out-dir' or arg == '--color':  # ignored
        i += 1
      elif arg.startswith('--error-format=') or arg.startswith('--json='):
        _ = arg  # ignored
      elif arg.startswith('--emit='):
        self.emit_list = arg.replace('--emit=', '')
      elif arg.startswith('--edition='):
        self.edition = arg.replace('--edition=', '')
      else:
        self.errors += 'ERROR: unknown ' + arg + '\n'
      i += 1
    if not self.crate_name:
      self.errors += 'ERROR: missing --crate-name\n'
    if not self.main_src:
      self.errors += 'ERROR: missing main source file\n'
    else:
      self.srcs.append(self.main_src)
    if not self.crate_type:
      # Treat "--cfg test" as "--test"
      if 'test' in self.cfgs:
        self.crate_type = 'test'
      else:
        self.errors += 'ERROR: missing --crate-type\n'
    if not self.root_pkg:
      self.root_pkg = self.crate_name
    if self.target:
      self.device_supported = True
    self.host_supported = True  # assume host supported for all builds
    self.cfgs = sorted(set(self.cfgs))
    self.features = sorted(set(self.features))
    self.codegens = sorted(set(self.codegens))
    self.externs = sorted(set(self.externs))
    self.core_externs = sorted(set(self.core_externs))
    self.static_libs = sorted(set(self.static_libs))
    self.shared_libs = sorted(set(self.shared_libs))
    self.decide_module_type()
    self.module_name = altered_name(self.stem)
    return self

  def dump_line(self):
    self.write('\n// Line ' + str(self.line_num) + ' ' + self.line)

  def feature_list(self):
    """Return a string of main_src + "feature_list"."""
    pkg = self.main_src
    if pkg.startswith('.../'):  # keep only the main package name
      pkg = re.sub('/.*', '', pkg[4:])
    if not self.features:
      return pkg
    return pkg + ' "' + ','.join(self.features) + '"'

  def dump_skip_crate(self, kind):
    if self.debug:
      self.write('\n// IGNORED: ' + kind + ' ' + self.main_src)
    return self

  def skip_crate(self):
    """Return crate_name or a message if this crate should be skipped."""
    if is_build_crate_name(self.crate_name):
      return self.crate_name
    if is_dependent_file_path(self.main_src):
      return 'dependent crate'
    return ''

  def dump(self):
    """Dump all error/debug/module code to the output .bp file."""
    self.runner.init_bp_file(self.outf_name)
    with open(self.outf_name, 'a') as outf:
      self.outf = outf
      if self.errors:
        self.dump_line()
        self.write(self.errors)
      elif self.skip_crate():
        self.dump_skip_crate(self.skip_crate())
      else:
        if self.debug:
          self.dump_debug_info()
        self.dump_android_module()

  def dump_debug_info(self):
    """Dump parsed data, when cargo2android is called with --debug."""

    def dump(name, value):
      self.write('//%12s = %s' % (name, value))

    def opt_dump(name, value):
      if value:
        dump(name, value)

    def dump_list(fmt, values):
      for v in values:
        self.write(fmt % v)

    self.dump_line()
    dump('module_name', self.module_name)
    dump('crate_name', self.crate_name)
    dump('crate_type', self.crate_type)
    dump('main_src', self.main_src)
    dump('has_warning', self.has_warning)
    dump('for_host', self.host_supported)
    dump('for_device', self.device_supported)
    dump('module_type', self.module_type)
    opt_dump('target', self.target)
    opt_dump('edition', self.edition)
    opt_dump('emit_list', self.emit_list)
    opt_dump('cap_lints', self.cap_lints)
    dump_list('//         cfg = %s', self.cfgs)
    dump_list('//         cfg = \'feature "%s"\'', self.features)
    # TODO(chh): escape quotes in self.features, but not in other dump_list
    dump_list('//     codegen = %s', self.codegens)
    dump_list('//     externs = %s', self.externs)
    dump_list('//   -l static = %s', self.static_libs)
    dump_list('//  -l (dylib) = %s', self.shared_libs)

  def dump_android_module(self):
    """Dump one Android module definition."""
    if not self.module_type:
      self.write('\nERROR: unknown crate_type ' + self.crate_type)
      return
    self.write('\n' + self.module_type + ' {')
    self.dump_android_core_properties()
    if self.edition:
      self.write('    edition: "' + self.edition + '",')
    self.dump_android_property_list('features', '"%s"', self.features)
    cfg_fmt = '"--cfg %s"'
    if self.cap_lints:
      allowed = '"--cap-lints ' + self.cap_lints + '"'
      if not self.cfgs:
        self.write('    flags: [' + allowed + '],')
      else:
        self.write('    flags: [\n       ' + allowed + ',')
        self.dump_android_property_list_items(cfg_fmt, self.cfgs)
        self.write('    ],')
    else:
      self.dump_android_property_list('flags', cfg_fmt, self.cfgs)
    if self.externs:
      self.dump_android_externs()
    self.dump_android_property_list('static_libs', '"lib%s"', self.static_libs)
    self.dump_android_property_list('shared_libs', '"lib%s"', self.shared_libs)
    self.write('}')

  def test_module_name(self):
    """Return a unique name for a test module."""
    # first+middle+last = root_pkg+crate_name+source_file_path
    first_name = pkg2crate_name(self.root_pkg)
    last_name = re.sub('/', '_', re.sub('.rs$', '', self.main_src))
    middle_name = self.crate_name
    # Simplify middle_name if it is already part of first_name or last_name.
    if first_name.startswith(middle_name) or last_name.endswith(middle_name):
      middle_name = 'test'
    last_name = pkg2crate_name(last_name)
    if middle_name in last_name:
      return self.root_pkg + '_' + last_name
    else:
      return self.root_pkg + '_' + middle_name + '_' + last_name

  def decide_module_type(self):
    """Decide which Android module type to use."""
    host = '' if self.device_supported else '_host'
    if self.crate_type == 'bin':  # rust_binary[_host]
      self.module_type = 'rust_binary' + host
      self.stem = self.crate_name
    elif self.crate_type == 'lib':  # rust_library[_host]_rlib
      self.module_type = 'rust_library' + host + '_rlib'
      self.stem = 'lib' + self.crate_name
    elif self.crate_type == 'cdylib':  # rust_library[_host]_dylib
      # TODO(chh): complete and test cdylib module type
      self.module_type = 'rust_library' + host + '_dylib'
      self.stem = 'lib' + self.crate_name + '.so'
    elif self.crate_type == 'test':  # rust_test[_host]
      self.module_type = 'rust_test' + host
      self.stem = self.test_module_name()
      # self.stem will be changed after merging with other tests.
      # self.stem is NOT used for final test binary name.
      # rust_test uses each source file base name as its output file name.
    elif self.crate_type == 'proc-macro':  # rust_proc_macro
      self.module_type = 'rust_proc_macro'
      self.stem = 'lib' + self.crate_name
    else:  # unknown module type, rust_prebuilt_dylib? rust_library[_host]?
      self.module_type = ''
      self.stem = ''

  def dump_android_property_list_items(self, fmt, values):
    for v in values:
      # fmt has quotes, so we need escape_quotes(v)
      self.write('        ' + (fmt % escape_quotes(v)) + ',')

  def dump_android_property_list(self, name, fmt, values):
    if values:
      self.write('    ' + name + ': [')
      self.dump_android_property_list_items(fmt, values)
      self.write('    ],')

  def dump_android_core_properties(self):
    """Dump the module header, name, stem, etc."""
    self.write('    name: "' + self.module_name + '",')
    if self.stem != self.module_name:
      self.write('    stem: "' + self.stem + '",')
    if self.has_warning and not self.cap_lints:
      self.write('    deny_warnings: false,')
    if self.host_supported and self.device_supported:
      self.write('    host_supported: true,')
    self.write('    crate_name: "' + self.crate_name + '",')
    if len(self.srcs) > 1:
      self.srcs = sorted(set(self.srcs))
      self.dump_android_property_list('srcs', '"%s"', self.srcs)
    else:
      self.write('    srcs: ["' + self.main_src + '"],')
    if self.crate_type == 'test':
      # When main_src is src/lib.rs, the crate_name is same as parent crate
      # When main_src is tests/foo.rs, the crate_name is foo
      self.write('    relative_install_path: "rust/' + self.root_pkg + '",')

  def dump_android_externs(self):
    """Dump the dependent rlibs and dylibs property."""
    so_libs = list()
    rust_libs = ''
    deps_libname = re.compile('^.* = lib(.*)-[0-9a-f]*.(rlib|so|rmeta)$')
    for lib in self.externs:
      # normal value of lib: "libc = liblibc-*.rlib"
      # strange case in rand crate:  "getrandom_package = libgetrandom-*.rlib"
      # we should use "libgetrandom", not "lib" + "getrandom_package"
      groups = deps_libname.match(lib)
      if groups is not None:
        lib_name = groups.group(1)
      else:
        lib_name = re.sub(' .*$', '', lib)
      if lib.endswith('.rlib') or lib.endswith('.rmeta'):
        # On MacOS .rmeta is used when Linux uses .rlib or .rmeta.
        rust_libs += '        "' + altered_name('lib' + lib_name) + '",\n'
      elif lib.endswith('.so'):
        so_libs.append(lib_name)
      else:
        rust_libs += '        // ERROR: unknown type of lib ' + lib_name + '\n'
    if rust_libs:
      self.write('    rlibs: [\n' + rust_libs + '    ],')
    # Are all dependent .so files proc_macros?
    # TODO(chh): Separate proc_macros and dylib.
    self.dump_android_property_list('proc_macros', '"lib%s"', so_libs)


class Runner(object):
  """Main class to parse cargo -v output and print Android module definitions."""

  def __init__(self, args):
    self.bp_files = set()  # Remember all output Android.bp files.
    # Saved flags, modes, and data.
    self.args = args
    self.dry_run = not args.run
    self.skip_cargo = args.skipcargo
    # Default action is cargo clean, followed by build or user given actions.
    if args.cargo:
      self.cargo = ['clean'] + args.cargo
    else:
      self.cargo = ['clean', 'build']
      default_target = '--target x86_64-unknown-linux-gnu'
      if args.device:
        self.cargo.append('build ' + default_target)
        if args.tests:
          self.cargo.append('build --tests')
          self.cargo.append('build --tests ' + default_target)
      elif args.tests:
        self.cargo.append('build --tests')

  def init_bp_file(self, name):
    if name not in self.bp_files:
      self.bp_files.add(name)
      with open(name, 'w') as outf:
        outf.write(ANDROID_BP_HEADER)

  def run_cargo(self):
    """Calls cargo -v and save its output to ./cargo.out."""
    if self.skip_cargo:
      return self
    cargo = './Cargo.toml'
    if not os.access(cargo, os.R_OK):
      print('ERROR: Cannot find or read', cargo)
      return self
    if not self.dry_run and os.path.exists('cargo.out'):
      os.remove('cargo.out')
    cmd_tail = ' --target-dir ' + TARGET_TMP + ' >> cargo.out 2>&1'
    for c in self.cargo:
      features = ''
      if self.args.features and c != 'clean':
        features = ' --features ' + self.args.features
      cmd = 'cargo -v ' + c + features + cmd_tail
      if self.args.rustflags and c != 'clean':
        cmd = 'RUSTFLAGS="' + self.args.rustflags + '" ' + cmd
      if self.dry_run:
        print('Dry-run skip:', cmd)
      else:
        if self.args.verbose:
          print('Running:', cmd)
        with open('cargo.out', 'a') as cargo_out:
          cargo_out.write('### Running: ' + cmd + '\n')
        os.system(cmd)
    return self

  def dump_dependencies(self, dependencies):
    """Append dependencies and their features to Android.bp."""
    if not dependencies:
      return
    dependent_list = list()
    for c in dependencies:
      dependent_list.append(c.feature_list())
    sorted_dependencies = sorted(set(dependent_list))
    self.init_bp_file('Android.bp')
    with open('Android.bp', 'a') as outf:
      outf.write('\n// dependent_library ["feature_list"]\n')
      for s in sorted_dependencies:
        outf.write('//   ' + s + '\n')

  def gen_bp(self):
    """Parse cargo.out and generate Android.bp files."""
    if self.dry_run:
      print('Dry-run skip: read', CARGO_OUT, 'write Android.bp')
    elif os.path.exists(CARGO_OUT):
      with open(CARGO_OUT, 'r') as cargo_out:
        crates, dependencies = self.parse(cargo_out, 'Android.bp')
        crates.sort(key=get_module_name)
        for c in crates:
          c.dump()
        if self.args.dependencies and dependencies:
          self.dump_dependencies(dependencies)
    return self

  def add_crate(self, crates, crate, dependencies):
    """Merge crate with someone in crates, or append to it. Return crates."""
    if crate.skip_crate():
      if self.args.debug:  # include debug info of all crates
        crates.append(crate)
      if self.args.dependencies:  # include only dependent crates
        if (is_dependent_file_path(crate.main_src) and
            not is_build_crate_name(crate.crate_name)):
          dependencies.append(crate)
    else:
      for c in crates:
        if c.merge(crate, 'Android.bp'):
          return crates
      crates.append(crate)
    return crates

  def find_warning_owners(self, crates, warning_files):
    """For each warning file, find its owner crate."""
    missing_owner = False
    for f in warning_files:
      cargo_dir = ''  # find lowest crate, with longest path
      owner = None  # owner crate of this warning
      for c in crates:
        if (f.startswith(c.cargo_dir + '/') and
            len(cargo_dir) < len(c.cargo_dir)):
          cargo_dir = c.cargo_dir
          owner = c
      if owner:
        owner.has_warning = True
      else:
        missing_owner = True
    if missing_owner and os.path.exists('Cargo.toml'):
      # owner is the root cargo, with empty cargo_dir
      for c in crates:
        if not c.cargo_dir:
          c.has_warning = True

  def parse(self, inf, outf_name):
    """Parse rustc and warning messages in inf, return a list of Crates."""
    crates = list()
    dependencies = list()  # dependent and build script crates
    warning_files = set()  # files with warnings
    n = 0  # line number
    prev_warning = False  # true if previous line was warning: ...
    for line in inf:
      n += 1
      is_warning = line.startswith('warning: ')
      if not is_warning:
        groups = RUSTC_PAT.match(line)
        if groups is not None:
          crate = Crate(self, outf_name).parse(n, groups.group(1))
          crates = self.add_crate(crates, crate, dependencies)
        elif prev_warning:
          groups = WARNING_FILE_PAT.match(line)
          if groups is not None:
            fpath = groups.group(1)
            if fpath[0] != '/':  # ignore absolute path
              warning_files.add(fpath)
      prev_warning = is_warning
    self.find_warning_owners(crates, warning_files)
    return crates, dependencies


def parse_args():
  """Parse main arguments."""
  parser = argparse.ArgumentParser('cargo2android')
  parser.add_argument(
      '--cargo',
      action='append',
      metavar='args_string',
      help=('extra cargo build -v args in a string, ' +
            'each --cargo flag calls cargo build -v once'))
  parser.add_argument(
      '--debug',
      action='store_true',
      default=False,
      help='dump debug info into Android.bp')
  parser.add_argument(
      '--dependencies',
      action='store_true',
      default=False,
      help='dump debug info of dependent crates')
  parser.add_argument(
      '--device',
      action='store_true',
      default=False,
      help='run cargo also for a default device target')
  parser.add_argument(
      '--features', type=str, help='passing features to cargo build')
  parser.add_argument(
      '--onefile',
      action='store_true',
      default=False,
      help=('output all into one ./Android.bp, default will generate ' +
            'one Android.bp per Cargo.toml in subdirectories'))
  parser.add_argument(
      '--run',
      action='store_true',
      default=False,
      help='run it, default is dry-run')
  parser.add_argument('--rustflags', type=str, help='passing flags to rustc')
  parser.add_argument(
      '--skipcargo',
      action='store_true',
      default=False,
      help='skip cargo command, parse cargo.out, and generate Android.bp')
  parser.add_argument(
      '--tests',
      action='store_true',
      default=False,
      help='run cargo build --tests after normal build')
  parser.add_argument(
      '--verbose',
      action='store_true',
      default=False,
      help='echo executed commands')
  return parser.parse_args()


def main():
  args = parse_args()
  if not args.run:  # default is dry-run
    print(DRY_RUN_NOTE)
  Runner(args).run_cargo().gen_bp()


if __name__ == '__main__':
  main()
