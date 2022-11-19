use anyhow::bail;
use anyhow::Context;
use std::collections::BTreeMap;
use std::collections::BTreeSet;
use anyhow::Result;
use clap::Parser;
use std::fs::File;
use std::io::Write;
use std::path::Path;
use std::path::PathBuf;
use std::process::Command;
use regex::Regex;
use once_cell::sync::Lazy;

/// TODO
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// Use cargo in the cargo_bin directory instead of the prebuilt one
    #[arg(long)]
    cargo_bin: Option<PathBuf>,

    /// Config file.
    #[arg(long)]
    cfg: PathBuf,

    /// Skip the `cargo build` commands and reuse the "cargo.out" file from a previous run.
    #[arg(long)]
    reuse_cargo_out: bool,
}

#[derive(serde::Deserialize)]
#[serde(deny_unknown_fields)]
struct Config {
    tests: bool,
    #[serde(default)]
    features: Vec<String>,
    #[serde(default)]
    workspace: bool,
    #[serde(default)]
    workspace_excludes: Vec<String>,
    global_defaults: Option<String>,
    #[serde(default)]
    apex_available: Vec<String>,
    #[serde(default)]
    module_name_overrides: BTreeMap<String, String>,
    #[serde(default)]
    package: BTreeMap<String, PackageConfig>,
    /// Modules in this list will not be output.
    #[serde(default)]
    module_blocklist: Vec<String>,
}

/// Options that apply to everything in a package (i.e. everything associated with a particular
/// Cargo.toml file).
#[derive(serde::Deserialize, Default)]
#[serde(deny_unknown_fields)]
struct PackageConfig {
    #[serde(default)]
    device_supported: Option<bool>, // default true
    #[serde(default)]
    host_supported: Option<bool>, // default true
    #[serde(default)]
    force_rlib: bool,
    // TODO: should probably be a list of modules instead of whole crates. crates can have a mix of
    // unit and integration etsts.
    #[serde(default)]
    no_presubmit: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();
    let cfg: Config = toml::from_str(&std::fs::read_to_string(&args.cfg).with_context(|| format!("failed to read file: {:?}", args.cfg))?).context("failed to parse config")?;

    let root_manifest = cargo_toml::Manifest::from_str(&std::fs::read_to_string("Cargo.toml")?)?;
    let root_package_name = root_manifest.package.expect("must have [package]").name;

    // Add the custom cargo to PATH.
    // NOTE: If the directory with cargo has more binaries, this could have some unpredictable side
    // effects. That is partly intended though, because we want to use that cargo binary's
    // associated rustc.
    if let Some(cargo_bin) = args.cargo_bin {
        let path = std::env::var_os("PATH").unwrap();
        let mut paths = std::env::split_paths(&path).collect::<Vec<_>>();
        paths.push(PathBuf::from(cargo_bin.parent().unwrap()));
        let new_path = std::env::join_paths(paths)?;
        std::env::set_var("PATH", &new_path);
    }

    if !args.reuse_cargo_out {
        let mut cargo_out_file = std::fs::File::create("cargo.out")?;

        // cargo clean
        run_cargo(&mut cargo_out_file, Command::new("cargo").arg("clean"))?;

        let default_target = "x86_64-unknown-linux-gnu";
        let feature_args = if cfg.features.is_empty() {
            vec![]
        } else {
            vec!["--no-default-features".to_string(), "--features".to_string(), cfg.features.join(",")]
        };

        let workspace_args = if cfg.workspace {
            let mut v = vec!["--workspace".to_string()];
            if !cfg.workspace_excludes.is_empty() {
                for x in cfg.workspace_excludes.iter() {
                    v.push("--exclude".to_string());
                    v.push(x.clone());
                }
            }
            v
        } else {
            vec![]
        };
       
        // cargo build
        run_cargo(
            &mut cargo_out_file,
            Command::new("cargo")
                .args(["build", "--target", default_target])
                .args(workspace_args.clone())
                .args(feature_args.clone()),
        )?;

        if cfg.tests {
            // cargo build --tests
            // NOTE: We build --tests as a second step so that we know which dependencies, etc are
            // only needed for tests.
            run_cargo(
                &mut cargo_out_file,
                Command::new("cargo")
                    .args(["build", "--target", default_target, "--tests"])
                    .args(workspace_args.clone())
                    .args(feature_args.clone()),
            )?;
        }
    }

    // TODO: handle out files

    let cargo_out = CargoOut::parse(&std::fs::read_to_string("cargo.out")?)?;
    // eprintln!("cargo_out:\n{:#?}", cargo_out);

    assert!(cargo_out.cc_invocations.is_empty());
    assert!(cargo_out.ar_invocations.is_empty());

    // cargo out => crates
    let mut crates = Vec::new();
    for rustc in cargo_out.rustc_invocations.iter() {
        let c = Crate::from_rustc_invocation(rustc).with_context(|| format!("failed to process rustc invocation: {rustc}"))?;
        if c.name.starts_with("build_script_") || c.crate_dir.starts_with("/") {
            continue;
        }
        // TODO: merge logic. do we actually need this for crosvm? might only be needed when using
        // extra cargo invocations with custom flags.
        crates.push(c);
    }
    // eprintln!("\n\ncrates:\n{:#?}", crates);

    // group by bp file
    let mut bp_modules: BTreeMap<PathBuf, Vec<Crate>> = BTreeMap::new();  // bp file path => Vec<Crates>
    for c in crates {
        let cargo_toml_path = c.crate_dir.join("Cargo.toml");
        assert!(cargo_toml_path.exists(), "missing file: {:?}", cargo_toml_path);
        let bp_path = c.crate_dir.join("Android.bp");
        bp_modules.entry(bp_path).or_default().push(c);
    }
    // write bp files
    for (bp_path, crates) in bp_modules {
        // Keep the old license header.
        // TODO: add some sentinel lines around the generated modules instead. then, people can
        // easily add anything above or below.
        let license_section = match std::fs::read_to_string(&bp_path) {
            Ok(s) =>  
                s.lines()
                .skip_while(|l| l.starts_with("//"))
                .take_while(|l| !l.starts_with("rust_") && !l.starts_with("genrule {"))
                .collect::<Vec<&str>>().join("\n"),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => "// TODO: Add license.".to_string(),
            Err(e) => bail!("error when reading {bp_path:?}: {e}"),
        };

        let mut bp_contents = String::new();
        bp_contents += "// This file is generated by cargo2android.\n";
        bp_contents += "// Do not modify this file as changes will be overridden on upgrade.\n\n";
        bp_contents += license_section.trim();
        bp_contents += "\n";
        // TODO: handle "copy_out" gen rules (e.g. protobufs)
        let mut modules = Vec::new();
        for c in &crates {
            modules.extend(c.to_bp_modules(&cfg)?);
        }

        // TODO: old "rust_defaults" behavior requires more thought to emualate. Maybe not worth
        // it.
        //
        // let (mut test_modules, non_test_modules) = modules.into_iter().partition::<Vec<_>, _>(|m| m.module_type.starts_with("rust_test"));
        // maybe_add_defaults(crates[0].package_name.clone() + "_test_defaults", &mut test_modules);
        // let mut modules: Vec<_> = test_modules.into_iter().chain(non_test_modules.into_iter()).collect();

        modules.sort_by_key(|m| m.props.get_string("name").to_string());
        for m in modules {
            m.write(&mut bp_contents)?;
            bp_contents += "\n";
        }
        File::create(&bp_path)?.write_all(bp_contents.as_bytes())?;

        let bpfmt_output = Command::new("bpfmt")
            .args(["-w", &bp_path.to_string_lossy()])
            .output()?;
        if !bpfmt_output.status.success() {
            eprintln!("WARNING: bpfmt -w {:?} failed: {}", bp_path, String::from_utf8_lossy(&bpfmt_output.stderr));
        }
    }

    Ok(())
}

fn run_cargo(cargo_out: &mut impl std::io::Write, cmd: &mut Command) -> Result<()> {
    cmd.arg("-v");
    cmd.args(["--target-dir", "target.tmp"]);

    let output = cmd.output()?;
    cargo_out.write_all(&output.stdout)?;
    cargo_out.write_all(&output.stderr)?;
    if !output.status.success() {
        eprintln!("Running: {:?}\n", cmd);
        eprintln!("cargo stderr:\n{}", String::from_utf8(output.stderr).unwrap());
        bail!("bad exit status: {:?}", output.status);
    }
    Ok(())
}

/// Raw-ish data extracted from cargo.out file.
#[derive(Debug, Default)]
struct CargoOut {
    rustc_invocations: Vec<String>,

    // package name => cmd args
    cc_invocations: BTreeMap<String, String>,
    ar_invocations: BTreeMap<String, String>,

    // lines starting with "warning: ".
    // line number => line
    warning_lines: BTreeMap<usize, String>,
    warning_files: Vec<String>,

    errors: Vec<String>,
    test_errors: Vec<String>,
}

/// Info extracted from `CargoOut` for a crate.
///
/// Note that there is a 1-to-many relationship between a Cargo.toml file and these `Crate`
/// objects. For example, a Cargo.toml file might have a bin, a lib, and various tests. Each of
/// those will be a separate `Crate`. All of them will ahve the same `package_name`.
#[derive(Debug, Default)]
struct Crate {
    name: String,
    package_name: String,  // usually equal to `name`, except for, e.g., tests
    version: Option<String>,
    // cargo calls rustc with multiple --crate-type flags.
    // rustc can accept:
    //   --crate-type [bin|lib|rlib|dylib|cdylib|staticlib|proc-macro]
    types: Vec<String>,
    test: bool, // --test
    target: Option<String>, // --target
    features: Vec<String>,  // --cfg feature=
    cfgs: Vec<String>,  // non-feature --cfg
    externs: Vec<(String, Option<String>)>,  // name => rlib file
    codegens: Vec<String>,  // -C
    cap_lints: String,
    static_libs: Vec<String>,
    shared_libs: Vec<String>,
    emit_list: String,
    edition: cargo_toml::Edition,
    crate_dir: PathBuf,
    main_src: PathBuf, // relative to crate_dir
}

impl Crate {
    fn from_rustc_invocation(rustc: &str) -> Result<Crate> {
        let mut out = Crate::default();

        // split into args
        let args: Vec<&str> = rustc.split_whitespace().collect();
        let mut arg_iter = args.iter()
            // remove quotes from simple strings, panic for others
            .map(|arg| {
                match (arg.chars().nth(0), arg.chars().skip(1).last()) {
                    (Some('"'), Some('"')) => &arg[1..arg.len()-1],
                    (Some('\''), Some('\'')) => &arg[1..arg.len()-1],
                    (Some('"'), None) => panic!("can't handle strings with whitespace"),
                    (Some('\''), None) => panic!("can't handle strings with whitespace"),
                    _ => arg,
                }
            });
        // process each arg
        while let Some(arg) = arg_iter.next() {
            match arg {
                "--crate-name" => out.name = arg_iter.next().unwrap().to_string(),
                "--crate-type" => out.types.push(arg_iter.next().unwrap().to_string()),
                "--test" => out.test = true,
                "--target" => out.target = Some(arg_iter.next().unwrap().to_string()),
                "--cfg" => {
                    // example: feature=\"sink\"
                    let arg = arg_iter.next().unwrap();
                    if let Some(feature) = arg.strip_prefix("feature=\"").and_then(|s| s.strip_suffix("\"")) {
                        out.features.push(feature.to_string());
                    } else {
                        out.cfgs.push(arg.to_string());
                    }
                },
                "--extern" => {
                    // example: proc_macro
                    // example: memoffset=/some/path/libmemoffset-2cfda327d156e680.rmeta
                    let arg = arg_iter.next().unwrap();
                    if let Some((name, path)) = arg.split_once("=") {
                        out.externs.push((name.to_string(), Some(path.split("/").last().unwrap().to_string())));
                    } else {
                        out.externs.push((arg.to_string(), None));
                    }
                },
                _ if arg.starts_with("-C") => {
                    // handle both "-Cfoo" and "-C foo"
                    let arg = if arg == "-C" {
                        arg_iter.next().unwrap()
                    } else {
                        arg.strip_prefix("-C").unwrap()
                    };
                    // 'prefer-dynamic' does not work with common flag -C lto
                    // 'embed-bitcode' is ignored; we might control LTO with other .bp flag
                    // 'codegen-units' is set in Android global config or by default
                    //
                    // TODO: this is business logic. move it out of the parsing code
                    if !arg.starts_with("codegen-units=") &&
                       !arg.starts_with("debuginfo=") &&
                       !arg.starts_with("embed-bitcode=") &&
                       !arg.starts_with("extra-filename=") &&
                       !arg.starts_with("incremental=") &&
                       !arg.starts_with("metadata=") &&
                       arg != "prefer-dynamic" {
                        out.codegens.push(arg.to_string());
                    }
                },
                "--cap-lints" => out.cap_lints = arg_iter.next().unwrap().to_string(),
                "-L" => {
                    // ignore
                    //
                    // cargo2android.py uses this to determine the root package. unclear why
                    arg_iter.next().unwrap();
                }
                "-l" => {
                    let arg = arg_iter.next().unwrap();
                    if let Some(lib) = arg.strip_prefix("static=") {
                        out.static_libs.push(lib.to_string());
                    } else if let Some(lib) = arg.strip_prefix("dylib=") {
                        out.shared_libs.push(lib.to_string());
                    } else {
                        out.shared_libs.push(arg.to_string());
                    }
                }
                _ if arg.starts_with("--emit=") => {
                    out.emit_list = arg.strip_prefix("--emit=").unwrap().to_string();
                }
                _ if !arg.starts_with("-") => {
                    let src_path = Path::new(arg);
                    out.crate_dir = src_path.parent().unwrap().to_path_buf();
                    while !out.crate_dir.join("Cargo.toml").try_exists()? {
                        if let Some(parent) = out.crate_dir.parent() {
                            out.crate_dir = parent.to_path_buf();
                        } else {
                            bail!("No Cargo.toml found in parents of {:?}", src_path);
                        }
                    }
                    if out.crate_dir.file_name().map_or(false, |x| x == "src") {
                        out.crate_dir = out.crate_dir.parent().unwrap().to_path_buf();
                    }
                    out.main_src = src_path.strip_prefix(&out.crate_dir).unwrap().to_path_buf();
                    // shorten imported crate main source paths like $HOME/.cargo/
                    // registry/src/github.com-1ecc6299db9ec823/memchr-2.3.3/src/lib.rs
                    // out.main_src = re.sub(r'^/[^ ]*/registry/src/', '.../', arg)
                    // out.main_src = re.sub(r'^\.\.\./github.com-[0-9a-f]*/', '.../', out.main_src)
                }

                // ignored flags
                "--out-dir" => { arg_iter.next().unwrap(); /* ignore */ }
                "--color" => { arg_iter.next().unwrap(); /* ignore */ }
                _ if arg.starts_with("--error-format=") => { /* ignore */ }
                _ if arg.starts_with("--edition=") => { /* ignore */ }
                _ if arg.starts_with("--json=") => { /* ignore */ }
                _ if arg.starts_with("-Aclippy") => { /* ignore */ }
                _ if arg.starts_with("-Wclippy") => { /* ignore */ }
                "-W" => { /* ignore */ }
                "-D" => { /* ignore */ }

                arg => bail!("unsupported rustc argument: {arg:?}"),
            }
        }

        if out.name.is_empty() {
            bail!("missing --crate-name");
        }
        if out.main_src.as_os_str().is_empty() {
            bail!("missing main source file");
        }
        if !out.types.is_empty() == out.test {
            bail!("expected exactly one of either --crate-type or --test");
        }
        if out.types.iter().any(|x| x == "lib") && out.types.iter().any(|x| x == "rlib") {
            bail!("cannot both have lib and rlib crate types");
        }

        // Parse the cargo.toml and grab the package version.
        let manifest = cargo_toml::Manifest::from_str(&std::fs::read_to_string(out.crate_dir.join("Cargo.toml"))?)?;
        let package = manifest.package.expect("must have [package]");
        out.package_name = package.name.clone();
        out.version = Some(package.version.get()?.clone());
        out.edition = *package.edition.get()?;

        Ok(out)
    }

    /// Convert a `Crate` into `BpModule`s. This is were most of the messy business logic should
    /// live.
    fn to_bp_modules(&self, cfg: &Config) -> Result<Vec<BpModule>> {
        let mut out = Vec::new();
        let mut types = self.types.clone();
        if self.test {
            types.push("test".to_string());
        }
        for crate_type in types {
            let def = PackageConfig::default();
            let package_cfg = cfg.package.get(&self.package_name).unwrap_or(&def);

            let host = if package_cfg.device_supported.unwrap_or(true) { "" } else { "_host" };
            let rlib = if package_cfg.force_rlib { "_rlib" } else { "" };
            let (module_type, module_name, stem) = match crate_type.as_str() {
                "bin" => {
                    ("rust_binary".to_string() + host, self.name.clone(), self.name.clone())
                }
                "lib" | "rlib" => {
                    let stem = "lib".to_string() + &self.name;
                    ("rust_library".to_string() + rlib + host, stem.clone(), stem)
                }
                "dylib" => {
                    let stem = "lib".to_string() + &self.name;
                    ("rust_library".to_string() + host + "_dylib", stem.clone() + "_dylib", stem)
                }
                "cdylib" => {
                    let stem = "lib".to_string() + &self.name;
                    ("rust_ffi".to_string() + host + "_shared", stem.clone() + "_shared", stem)
                }
                "staticlib" => {
                    let stem = "lib".to_string() + &self.name;
                    ("rust_ffi".to_string() + host + "_static", stem.clone() + "_static", stem)
                }
                "proc-macro" => {
                    let stem = "lib".to_string() + &self.name;
                    ("rust_proc_macro".to_string(), stem.clone(), stem)
                }
                "test" => {
                    let suffix = self.main_src.to_string_lossy().to_owned();
                    let suffix = suffix.replace("/", "_").replace(".rs", "");
                    let stem = self.package_name.clone() + "_test_" + &suffix;
                    ("rust_test".to_string() + host, stem.clone(), stem)
                }
                _ => panic!("unexpected crate type: {}", crate_type),
            };

            let mut m = BpModule::new(module_type.clone());
            let module_name = cfg.module_name_overrides.get(&module_name).unwrap_or(&module_name);
            if cfg.module_blocklist.contains(module_name) {
                continue;
            }
            m.props.set("name", module_name.clone());
            if &stem != module_name {
                m.props.set("stem", stem);
            }

            if let Some(defaults) = &cfg.global_defaults {
                m.props.set("defaults", vec![defaults.clone()]);
            }

            if package_cfg.host_supported.unwrap_or(true) && package_cfg.device_supported.unwrap_or(true) && module_type != "rust_proc_macro" {
                m.props.set("host_supported", true);
            }

            m.props.set("crate_name", self.name.clone());
            m.props.set("cargo_env_compat", true);

            if let Some(version) = &self.version {
                m.props.set("cargo_pkg_version", version.clone());
            }

            if self.test {
                m.props.set("test_suites", vec!["general-tests"]);
                m.props.set("auto_gen_config", true);
                if package_cfg.host_supported.unwrap_or(true) {
                    m.props.object("test_options").set("unit_test", !package_cfg.no_presubmit);
                }
            }

            // TODO: add "copy_out" files
            m.props.set("srcs", vec![self.main_src.to_string_lossy().to_string()]);

            m.props.set("edition", (self.edition as u32).to_string());
            if !self.features.is_empty() {
                m.props.set("features", self.features.clone());
            }
            if !self.cfgs.is_empty() {
                m.props.set("cfgs", self.cfgs.clone());
            }

            let mut flags = Vec::new();
            if !self.cap_lints.is_empty() {
                flags.push(self.cap_lints.clone());
            }
            flags.extend(self.codegens.clone());
            if !flags.is_empty() {
                m.props.set("flags", flags);
            }

            let mut rust_libs = Vec::new();
            let mut proc_macro_libs = Vec::new();
            for (extern_name, filename) in &self.externs {
                if extern_name == "proc_macro" {
                    continue;
                }
                let filename = filename.as_ref().expect(&format!("no filename for {}", extern_name));
                // normal value of lib: "libc = liblibc-*.rlib"
                // strange case in rand crate:  "getrandom_package = libgetrandom-*.rlib"
                // we should use "libgetrandom", not "lib" + "getrandom_package"
                static REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^lib(.*)-[0-9a-f]*.(rlib|so|rmeta)$").unwrap());
                let lib_name = if let Some(x) = REGEX.captures(&filename).and_then(|x| x.get(1)) {
                    x
                } else {
                    bail!("bad filename for extern {}: {}", extern_name, filename);
                };
                if filename.ends_with(".rlib") || filename.ends_with(".rmeta") {
                    let module_name = "lib".to_string() + lib_name.as_str();
                    let module_name = cfg.module_name_overrides.get(&module_name).unwrap_or(&module_name);
                    rust_libs.push(module_name.to_string());
                } else if filename.ends_with(".so") {
                    // Assume .so files are always proc_macros. May not always be right.
                    proc_macro_libs.push("lib".to_string() + lib_name.as_str());
                } else {
                    unreachable!();
                }
            }
            if !rust_libs.is_empty() {
                m.props.set("rustlibs", rust_libs);
            }
            if !proc_macro_libs.is_empty() {
                m.props.set("proc_macros", proc_macro_libs);
            }
            if !self.static_libs.is_empty() {
                m.props.set("static_libs", self.static_libs.clone());
            }
            if !self.shared_libs.is_empty() {
                m.props.set("shared_libs", self.shared_libs.clone());
            }

            if !cfg.apex_available.is_empty() && ["lib", "rlib", "dylib", "staticlib", "cdylib"].contains(&crate_type.as_str()) {
                m.props.set("apex_available", cfg.apex_available.clone());
            }

            // TODO: "add_module_block" equivalent

            out.push(m);
        }
        Ok(out)
    }
}

// Create a "rust_defaults" module if there is overlap between the modules in a package.
fn maybe_add_defaults(defaults_module_name: String, modules: &mut Vec<BpModule>) {
    if modules.len() <= 1 {
        return;
    }

    let mut existing_defaults = modules.iter().map(|m| m.props.0.get("defaults")).collect::<Vec<_>>();
    existing_defaults.dedup();
    if existing_defaults.len() > 1 {
        return;
    }

    let mut common_keys = modules[0].props.0.keys().cloned().collect::<BTreeSet<_>>();
    for m in modules.iter().skip(1) {
        common_keys = common_keys.intersection(&m.props.0.keys().cloned().collect()).cloned().collect();
    }
    common_keys.remove("name");
    if common_keys.is_empty() {
        return;
    }

    let mut defaults = BpModule::new("rust_defaults".to_string());
    defaults.props.set("name", defaults_module_name.clone());
    for k in common_keys {
        let mut vs = modules.iter().map(|m| m.props.0.get(&k).unwrap()).collect::<Vec<_>>();
        vs.dedup();
        if vs.len() == 1 {
            defaults.props.set(&k, vs[0].clone());
            for m in modules.iter_mut() {
                m.props.0.remove(&k);
            }
        }
    }
    for m in modules.iter_mut() {
        m.props.set("defaults", defaults_module_name.clone());
    }
    if defaults.props.0.len() > 1 {
        modules.push(defaults);
    }
}

struct BpModule {
    module_type: String,
    props: BpProperties,
}

#[derive(Clone, PartialEq, Eq)]
struct BpProperties(BTreeMap<String, BpValue>);

#[derive(Clone, PartialEq, Eq)]
enum BpValue {
    Object(BpProperties),
    Bool(bool),
    String(String),
    List(Vec<BpValue>),
}

impl BpModule {
    fn new(module_type: String) -> BpModule {
        BpModule{module_type, props: BpProperties(BTreeMap::new())}
    }
    fn write(&self, w: &mut impl std::fmt::Write) -> Result<()> {
        w.write_str(&self.module_type)?;
        w.write_str(" ")?;
        self.props.write(w)?;
        w.write_str("\n")?;
        Ok(())
    }
}

impl BpProperties {
    fn get_string(&self, k: &str) -> &str {
        match self.0.get(k).unwrap() {
            BpValue::String(s) => &s,
            _ => unreachable!(),
        }
    }

    fn set<T: Into<BpValue>>(&mut self, k: &str, v: T) {
        self.0.insert(k.to_string(), v.into());
    }

    fn object(&mut self, k: &str) -> &mut BpProperties {
        let v = self.0.entry(k.to_string()).or_insert(BpValue::Object(BpProperties(BTreeMap::new())));
        match v {
            BpValue::Object(v) => v,
            _ => panic!("key {k:?} already has non-object value"),
        }
    }

    fn write(&self, w: &mut impl std::fmt::Write) -> Result<()> {
        w.write_str("{\n")?;
        let canonical_order = &[
            "name",
            "defaults",
            "stem",
            "host_supported",
            "prefer_rlib",
            "crate_name",
            "cargo_env_compat",
            "cargo_pkg_version",
            "srcs",
            "test_suites",
            "auto_gen_config",
            "test_options",
            "edition",
            "features",
            "rustlibs",
            "proc_macros",
            "arch",
            "target",
            "ld_flags",
            "apex_available",
        ];
        let mut props: Vec<(&String, &BpValue)> = self.0.iter().collect();
        props.sort_by_key(|(k, _)| {
            let i = canonical_order.iter().position(|x| k == x).unwrap_or(canonical_order.len());
            (i, k.clone())
        });
        for (k, v) in props {
            w.write_str(&k)?;
            w.write_str(": ")?;
            v.write(w)?;
            w.write_str(",\n")?;
        }
        w.write_str("}")?;
        Ok(())
    }
}

impl BpValue {
    fn write(&self, w: &mut impl std::fmt::Write) -> Result<()> {
        match self {
            BpValue::Object(p) => p.write(w)?,
            BpValue::Bool(b) => write!(w, "{b}")?,
            BpValue::String(s) => write!(w, "\"{s}\"")?,
            BpValue::List(vs) => {
                w.write_str("[")?;
                for (i, v) in vs.iter().enumerate() {
                    v.write(w)?;
                    if i != vs.len() - 1 {
                        w.write_str(", ")?;
                    }
                }
                w.write_str("]")?;
            }
        }
        Ok(())
    }
}

impl From<bool> for BpValue {
    fn from(x: bool) -> Self { BpValue::Bool(x) }
}

impl From<&str> for BpValue {
    fn from(x: &str) -> Self { BpValue::String(x.to_string()) }
}

impl From<String> for BpValue {
    fn from(x: String) -> Self { BpValue::String(x) }
}

impl<T: Into<BpValue>> From<Vec<T>> for BpValue {
    fn from(x: Vec<T>) -> Self { BpValue::List(x.into_iter().map(|x| x.into()).collect()) }
}

impl CargoOut {
    fn parse(contents: &str) -> Result<CargoOut> {
        // loop once to check for empty tests
        {
            let test_list_start_regex = Regex::new(r"^\s*Running (.*) \(.*\)$")?;
            let test_list_end_regex = Regex::new(r"^(\d+) tests?, (\d+) benchmarks?$")?;

            let mut cur_test_name = None;
            for (n, line) in contents.lines().enumerate() {
                if let Some(test_name) = test_list_start_regex.captures(line).and_then(|x| x.get(1)) {
                    cur_test_name = Some(test_name);
                } if let Some(test_name) = &cur_test_name {
                    if let Some((Some(test_count), Some(bench_count))) = test_list_end_regex.captures(line).map(|x| (x.get(1), x.get(2))) {
                        // add empty test?
                        // maybe check if the accumulated tests match the count
                    }
                }
            }
        }

        let mut result = CargoOut::default();
        let mut in_tests = false;
        let mut lines_iter = contents.lines().enumerate();
        loop {
            let (n, line) = match lines_iter.next() {
                Some(x) => x,
                None => break,
            };

            if line.starts_with("warning: ") {
                result.warning_lines.insert(n, line.to_string());
                continue;
            }

            // Cargo -v output of a call to rustc.
            static RUSTC_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^ +Running `rustc (.*)`$").unwrap());
            if let Some(args) = RUSTC_REGEX.captures(line).and_then(|x| x.get(1)) {
                result.rustc_invocations.push(args.as_str().to_string());
                continue;
            }
            // Cargo -vv output of a call to rustc could be split into multiple lines.
            // Assume that the first line will contain some CARGO_* env definition.
            static RUSTC_VV_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^ +Running `.*CARGO_.*=.*$").unwrap());
            if RUSTC_VV_REGEX.captures(line).is_some() {
                // cargo build -vv output can have multiple lines for a rustc command due to
                // '\n' in strings for environment variables.
                let mut line = line.to_string();
                loop {
                    // Use an heuristic to detect the completions of a multi-line command.
                    if line.ends_with("`") && line.chars().filter(|c| *c == '`').count() % 2 == 0 {
                        break;
                    }
                    if let Some((_, next_line)) = lines_iter.next() {
                        line += next_line;
                        continue;
                    }
                    break;
                }
                // The combined -vv output rustc command line pattern.
                static RUSTC_VV_CMD_ARGS: Lazy<Regex> = Lazy::new(|| Regex::new(r"^ *Running `.*CARGO_.*=.* rustc (.*)`$").unwrap());
                if let Some(args) = RUSTC_VV_CMD_ARGS.captures(&line).and_then(|x| x.get(1)) {
                    result.rustc_invocations.push(args.as_str().to_string());
                } else {
                    bail!("failed to parse cargo.out line: {}", line);
                }
                continue;
            }
            // Cargo -vv output of a "cc" or "ar" command; all in one line.
            static CC_AR_VV_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r#"^\[([^ ]*)[^\]]*\] running:? "(cc|ar)" (.*)$"#).unwrap());
            if let Some((Some(pkg), Some(cmd), Some(args))) = CC_AR_VV_REGEX.captures(line).map(|x| (x.get(1), x.get(2), x.get(3))) {
                match cmd.as_str() {
                    "ar" => result.ar_invocations.insert(pkg.as_str().to_string(), args.as_str().to_string()),
                    "cc" => result.cc_invocations.insert(pkg.as_str().to_string(), args.as_str().to_string()),
                    _ => unreachable!(),
                };
                continue;
            }
            // Rustc output of file location path pattern for a warning message.
            static WARNING_FILE_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^ *--> ([^:]*):[0-9]+").unwrap());
            if result.warning_lines.contains_key(&n.saturating_sub(1)) {
                if let Some(fpath) = WARNING_FILE_REGEX.captures(line).and_then(|x| x.get(1)) {
                    let fpath = fpath.as_str();
                    if !fpath.starts_with("/") {  // ignore absolute path. TODO: why?
                        result.warning_files.push(fpath.to_string());
                    }
                    continue;
                }
            }
            if line.starts_with("error: ") || line.starts_with("error[E") {
                if in_tests {
                    result.test_errors.push(line.to_string());
                } else {
                    result.errors.push(line.to_string());
                }
                continue;
            }
            static CARGO2ANDROID_RUNNING_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"^### Running: .*$").unwrap());
            if CARGO2ANDROID_RUNNING_REGEX.captures(line).is_some() {
                in_tests = line.contains("cargo test") && line.contains("--list");
                continue;
            }
        }

        // self.find_warning_owners()

        Ok(result)
    }
}
