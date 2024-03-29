// Copyright (C) 2024 The Android Open Source Project
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

//! Tool for downloading tombstones from the device and symbolizing them.

extern crate chrono;
extern crate clap;

use chrono::{DateTime, Datelike, Timelike};
use clap::Parser;
use std::env;
use std::fs::File;
use std::io::{stdout, BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, ExitCode, Stdio};

/// Downloads tombstones from the device and symbolizes them.
///
/// Paths to symbolized tombstones are written to stdout.
/// Requires Android 15 or later, or a rooted device.
#[derive(Parser, Debug)]
struct Args {
    /// Specify the path to a symbols directory.
    ///
    /// Must contain a .build-id subdirectory conforming to
    /// https://fedoraproject.org/wiki/RolandMcGrath/BuildID
    ///
    /// $ANDROID_PRODUCT_OUT/symbols is used as an additional symbols
    /// directory if $ANDROID_PRODUCT_OUT is set.
    #[arg(long, id = "DIR")]
    debug_file_directory: Vec<PathBuf>,

    /// Write tombstones to specified directory (default: current directory).
    #[arg(short, id = "OUT")]
    output_dir: Option<PathBuf>,

    /// Monitor for new tombstones after downloading existing tombstones
    /// instead of exiting; may not be reliable before Android 15.
    #[arg(short)]
    follow: bool,

    /// Download N most recent existing tombstones
    /// (default: 0 if -f specified, otherwise 3).
    #[arg(short, id = "N")]
    num_existing_tombstones: Option<usize>,

    /// Android device serial number (default: $ANDROID_SERIAL).
    #[arg(short, id = "SERIAL")]
    serial: Option<String>,
}

struct Acrash {
    debug_file_directory: Vec<PathBuf>,
    output_dir: PathBuf,
    follow: bool,
    num_existing_tombstones: usize,
    serial: Option<String>,
}

impl Acrash {
    fn new(args: Args) -> Acrash {
        let mut ac = Acrash {
            debug_file_directory: args.debug_file_directory,
            output_dir: args.output_dir.unwrap_or_else(|| env::current_dir().unwrap()),
            follow: args.follow,
            num_existing_tombstones: args.num_existing_tombstones.unwrap_or(if args.follow {
                0
            } else {
                3
            }),
            serial: args.serial,
        };
        let _ = env::var("ANDROID_PRODUCT_OUT")
            .inspect(|out| ac.debug_file_directory.push(PathBuf::from(out).join("symbols")));
        ac
    }

    fn adb_command(&self) -> Command {
        let mut cmd = Command::new("adb");
        if let Some(serial) = &self.serial {
            cmd.arg("-s").arg(serial);
        }
        cmd
    }

    fn stdout(cmd: &mut Command) -> Option<Vec<u8>> {
        let output = cmd.stderr(Stdio::inherit()).output().expect("command failed to start");
        if output.status.success() {
            Some(output.stdout)
        } else {
            eprintln!("{:?} failed", cmd);
            None
        }
    }

    fn call(cmd: &mut Command) -> Option<()> {
        let status = cmd.stderr(Stdio::inherit()).status().expect("command failed to start");
        if status.success() {
            Some(())
        } else {
            eprintln!("{:?} failed", cmd);
            None
        }
    }

    fn symbolize_tombstone(&self, name: &str) -> Option<()> {
        let device_pb = format!("/data/tombstones/{name}");
        let stat = String::from_utf8(Self::stdout(
            self.adb_command()
                .arg("shell")
                .arg("stat")
                .arg("-c")
                .arg("%Y.%y")
                .arg(device_pb.as_str()),
        )?)
        .unwrap();
        let mut parts = stat.split('.');
        let mtime_s = parts.next().unwrap().parse::<i64>().unwrap();
        parts.next(); // e.g. 2024-03-28 22:30:02
        let ns_part = parts.next().unwrap();
        let mtime_ns = ns_part[..ns_part.find(' ').unwrap()].parse::<u32>().unwrap();
        // TODO: Switch this to local time after re-adding local time support to chrono crate on
        // the host (see https://github.com/chronotope/chrono/pull/1018 for why this was disabled on
        // the device, but it doesn't need to be disabled on the host).
        let mtime = DateTime::from_timestamp(mtime_s, mtime_ns).unwrap();
        let host_pb = self.output_dir.join(format!(
            "tombstone_{:04}-{:02}-{:02}-{:02}-{:02}-{:02}-{:03}.pb",
            mtime.year(),
            mtime.month(),
            mtime.day(),
            mtime.hour(),
            mtime.minute(),
            mtime.second(),
            mtime.nanosecond() / 1000000
        ));
        let mut host_txt = host_pb.clone();
        host_txt.set_extension("txt");
        Self::call(self.adb_command().arg("pull").arg("-q").arg(device_pb.as_str()).arg(&host_pb))?;

        let mut pbtombstone = Command::new("pbtombstone");
        for dir in &self.debug_file_directory {
            pbtombstone.arg("--debug-file-directory");
            pbtombstone.arg(dir);
        }
        pbtombstone.arg(host_pb);

        let host_txt_file = File::create(&host_txt).unwrap();
        Self::call(pbtombstone.stdout(host_txt_file))?;
        stdout().write_all(host_txt.as_os_str().as_encoded_bytes()).unwrap();
        println!();

        Some(())
    }

    fn run(&self) -> Option<()> {
        if self.num_existing_tombstones != 0 {
            struct Tombstone {
                mtime: u64,
                name: String,
            }
            let mut pbtombstones = Vec::new();
            // adb ls *succeeds* if it's passed an inaccessible directory, and returns an empty
            // file list. Accessible directories will always have a "." entry, so to tell apart
            // inaccessible directories from empty ones, we keep track of whether we saw ".".
            let mut saw_dot = false;
            for line in Self::stdout(self.adb_command().arg("ls").arg("/data/tombstones"))?.lines()
            {
                let line = line.unwrap();
                let mut parts = line.split(' ');
                parts.next(); // mode
                parts.next(); // size
                let mtime = u64::from_str_radix(parts.next().unwrap(), 16).unwrap();
                let name = parts.next().unwrap();
                if name == "." {
                    saw_dot = true;
                }
                if name.ends_with(".pb") {
                    pbtombstones.push(Tombstone { mtime, name: name.to_string() })
                }
            }
            if !saw_dot {
                eprintln!("acrash: /data/tombstones inaccessible; this tool is only compatible with Android 15 and above");
                return None;
            }

            pbtombstones.sort_by_key(|t| t.mtime);
            for ts in &pbtombstones.as_slice()
                [pbtombstones.len().saturating_sub(self.num_existing_tombstones)..]
            {
                self.symbolize_tombstone(&ts.name)?;
            }
            if pbtombstones.is_empty() && !self.follow {
                eprintln!("acrash: no tombstones found");
                return None;
            }
        }

        // There's a race here between reading the file list and starting inotifyd that could cause
        // us to miss tombstones. But inotify is inherently capable of missing tombstones anyway
        // due to event queue overflows. In both cases, it is unlikely that we will miss a tombstone
        // because a prerequisite is that the system is producing tombstones at an unrealistically
        // high rate.
        if self.follow {
            let mut inotifyd = self
                .adb_command()
                .arg("shell")
                .arg("inotifyd")
                .arg("-")
                .arg("/data/tombstones:n")
                .stdout(Stdio::piped())
                .spawn()
                .expect("command failed to start");
            for line in BufReader::new(inotifyd.stdout.as_mut().unwrap()).lines() {
                let line = line.unwrap();
                let name = line.split('\t').nth(2).unwrap();
                if name.ends_with(".pb") {
                    self.symbolize_tombstone(name)?;
                }
            }
            let ecode = inotifyd.wait().expect("failed to wait on child");
            if !ecode.success() {
                return None;
            }
        }
        Some(())
    }
}

fn main() -> ExitCode {
    let args = Args::parse();
    if Acrash::new(args).run().is_some() {
        ExitCode::SUCCESS
    } else {
        ExitCode::FAILURE
    }
}
