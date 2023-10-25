// Copyright (C) 2023 The Android Open Source Project
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

//! Code for reading configuration json files.
//!
//! These are usually called `cargo_embargo.json`.

pub mod legacy;

use anyhow::{bail, Context, Result};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::BTreeMap;
use std::path::PathBuf;

fn default_apex_available() -> Vec<String> {
    vec!["//apex_available:platform".to_string(), "//apex_available:anyapex".to_string()]
}

fn is_default_apex_available(apex_available: &[String]) -> bool {
    apex_available == default_apex_available()
}

fn default_true() -> bool {
    true
}

fn is_true(value: &bool) -> bool {
    *value
}

fn is_false(value: &bool) -> bool {
    !*value
}

/// Options that apply to everything.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Config {
    pub variants: Vec<VariantConfig>,
    /// Package specific config options across all variants.
    #[serde(default, skip_serializing_if = "BTreeMap::is_empty")]
    pub package: BTreeMap<String, PackageConfig>,
}

impl Config {
    /// Names of all fields in [`Config`] other than `variants` (which is treated specially).
    const FIELD_NAMES: [&str; 1] = ["package"];

    /// Parses an instance of this config from a string of JSON.
    pub fn from_json_str(json_str: &str) -> Result<Self> {
        // First parse into untyped map.
        let mut config: Map<String, Value> =
            serde_json::from_str(json_str).context("failed to parse config")?;

        // Flatten variants. First, get the variants from the config file.
        let mut variants = match config.remove("variants") {
            Some(Value::Array(v)) => v,
            Some(_) => bail!("Failed to parse config: variants is not an array"),
            None => {
                // There are no variants, so just put everything into a single variant.
                vec![Value::Object(Map::new())]
            }
        };
        // Set default values in variants from top-level config.
        for variant in &mut variants {
            let variant = variant
                .as_object_mut()
                .context("Failed to parse config: variant is not an object")?;
            for (key, value) in &config {
                if key == "package" {
                    // Copy package entries across.
                    let variant_packages = variant
                        .entry("package")
                        .or_insert_with(|| Map::new().into())
                        .as_object_mut()
                        .context("Failed to parse config: variant package is not an object")?;
                    for (package_name, package_config) in value
                        .as_object()
                        .context("Failed to parse config: package is not an object")?
                    {
                        let variant_package = variant_packages
                            .entry(package_name)
                            .or_insert_with(|| Map::new().into())
                            .as_object_mut()
                            .context(
                                "Failed to parse config: variant package config is not an object",
                            )?;
                        for (package_key, package_value) in package_config
                            .as_object()
                            .context("Failed to parse config: package is not an object")?
                        {
                            if !PackageConfig::FIELD_NAMES.contains(&package_key.as_str())
                                && !variant_package.contains_key(package_key)
                            {
                                variant_package
                                    .insert(package_key.to_owned(), package_value.to_owned());
                            }
                        }
                    }
                } else if !variant.contains_key(key) {
                    variant.insert(key.to_owned(), value.to_owned());
                }
            }
        }
        // Remove other entries from the top-level config, and put variants back.
        config.retain(|key, _| Self::FIELD_NAMES.contains(&key.as_str()));
        if let Some(package) = config.get_mut("package") {
            for value in package
                .as_object_mut()
                .context("Failed to parse config: package is not an object")?
                .values_mut()
            {
                let package_config = value
                    .as_object_mut()
                    .context("Failed to parse config: package is not an object")?;
                package_config.retain(|key, _| PackageConfig::FIELD_NAMES.contains(&key.as_str()))
            }
        }
        config.insert("variants".to_string(), Value::Array(variants));

        // Parse into `Config` struct.
        serde_json::from_value(Value::Object(config)).context("failed to parse config")
    }

    /// Serializes an instance of this config to a string of pretty-printed JSON.
    pub fn to_json_string(&self) -> Result<String> {
        serde_json::to_string_pretty(self).context("failed to serialize config")
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct VariantConfig {
    /// Whether to output "rust_test" modules.
    #[serde(default, skip_serializing_if = "is_false")]
    pub tests: bool,
    /// Set of features to enable. If not set, uses the default crate features.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub features: Option<Vec<String>>,
    /// Whether to build with --workspace.
    #[serde(default, skip_serializing_if = "is_false")]
    pub workspace: bool,
    /// When workspace is enabled, list of --exclude crates.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub workspace_excludes: Vec<String>,
    /// Value to use for every generated module's "defaults" field.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub global_defaults: Option<String>,
    /// Value to use for every generated library module's "apex_available" field.
    #[serde(default = "default_apex_available", skip_serializing_if = "is_default_apex_available")]
    pub apex_available: Vec<String>,
    /// Value to use for every generated library module's `product_available` field.
    #[serde(default = "default_true", skip_serializing_if = "is_true")]
    pub product_available: bool,
    /// Value to use for every generated library module's `vendor_available` field.
    #[serde(default = "default_true", skip_serializing_if = "is_true")]
    pub vendor_available: bool,
    /// Minimum SDK version.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_sdk_version: Option<String>,
    /// Map of renames for modules. For example, if a "libfoo" would be generated and there is an
    /// entry ("libfoo", "libbar"), the generated module will be called "libbar" instead.
    ///
    /// Also, affects references to dependencies (e.g. in a "static_libs" list), even those outside
    /// the project being processed.
    #[serde(default, skip_serializing_if = "BTreeMap::is_empty")]
    pub module_name_overrides: BTreeMap<String, String>,
    /// Package specific config options.
    #[serde(default, skip_serializing_if = "BTreeMap::is_empty")]
    pub package: BTreeMap<String, PackageVariantConfig>,
    /// `cfg` flags in this list will not be included.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub cfg_blocklist: Vec<String>,
    /// Modules in this list will not be generated.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub module_blocklist: Vec<String>,
    /// Modules name => Soong "visibility" property.
    #[serde(default, skip_serializing_if = "BTreeMap::is_empty")]
    pub module_visibility: BTreeMap<String, Vec<String>>,
    /// Whether to run the cargo build and parse its output, rather than just figuring things out
    /// from the `cargo.metadata`.
    #[serde(default = "default_true", skip_serializing_if = "is_true")]
    pub run_cargo: bool,
}

impl Default for VariantConfig {
    fn default() -> Self {
        Self {
            tests: false,
            features: Default::default(),
            workspace: false,
            workspace_excludes: Default::default(),
            global_defaults: None,
            apex_available: default_apex_available(),
            product_available: true,
            vendor_available: true,
            min_sdk_version: None,
            module_name_overrides: Default::default(),
            package: Default::default(),
            cfg_blocklist: Default::default(),
            module_blocklist: Default::default(),
            module_visibility: Default::default(),
            run_cargo: true,
        }
    }
}

/// Options that apply to everything in a package (i.e. everything associated with a particular
/// Cargo.toml file), for all variants.
#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PackageConfig {
    /// File with content to append to the end of the generated Android.bp.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub add_toplevel_block: Option<PathBuf>,
    /// Patch file to apply after Android.bp is generated.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub patch: Option<PathBuf>,
}

impl PackageConfig {
    /// Names of all the fields on `PackageConfig`.
    const FIELD_NAMES: [&str; 2] = ["add_toplevel_block", "patch"];
}

/// Options that apply to everything in a package (i.e. everything associated with a particular
/// Cargo.toml file), for a particular variant.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PackageVariantConfig {
    /// Link against `alloc`. Only valid if `no_std` is also true.
    #[serde(default, skip_serializing_if = "is_false")]
    pub alloc: bool,
    /// Whether to compile for device. Defaults to true.
    #[serde(default = "default_true", skip_serializing_if = "is_true")]
    pub device_supported: bool,
    /// Whether to compile for host. Defaults to true.
    #[serde(default = "default_true", skip_serializing_if = "is_true")]
    pub host_supported: bool,
    /// Add a `compile_multilib: "first"` property to host modules.
    #[serde(default, skip_serializing_if = "is_false")]
    pub host_first_multilib: bool,
    /// Generate "rust_library_rlib" instead of "rust_library".
    #[serde(default, skip_serializing_if = "is_false")]
    pub force_rlib: bool,
    /// Whether to disable "unit_test" for "rust_test" modules.
    // TODO: Should probably be a list of modules or crates. A package might have a mix of unit and
    // integration tests.
    #[serde(default, skip_serializing_if = "is_false")]
    pub no_presubmit: bool,
    /// File with content to append to the end of each generated module.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub add_module_block: Option<PathBuf>,
    /// Modules in this list will not be added as dependencies of generated modules.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub dep_blocklist: Vec<String>,
    /// Don't link against `std`, only `core`.
    #[serde(default, skip_serializing_if = "is_false")]
    pub no_std: bool,
    /// Copy build.rs output to ./out/* and add a genrule to copy ./out/* to genrule output.
    /// For crates with code pattern:
    ///     include!(concat!(env!("OUT_DIR"), "/<some_file>.rs"))
    #[serde(default, skip_serializing_if = "is_false")]
    pub copy_out: bool,
    /// Add the given files to the given tests' `data` property. The key is the test source filename
    /// relative to the crate root.
    #[serde(default, skip_serializing_if = "BTreeMap::is_empty")]
    pub test_data: BTreeMap<String, Vec<String>>,
}

impl Default for PackageVariantConfig {
    fn default() -> Self {
        Self {
            alloc: false,
            device_supported: true,
            host_supported: true,
            host_first_multilib: false,
            force_rlib: false,
            no_presubmit: false,
            add_module_block: None,
            dep_blocklist: Default::default(),
            no_std: false,
            copy_out: false,
            test_data: Default::default(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn variant_config() {
        let config = Config::from_json_str(
            r#"{
            "tests": true,
            "package": {
                "argh": {
                    "patch": "patches/Android.bp.patch"
                },
                "another": {
                    "add_toplevel_block": "block.bp",
                    "device_supported": false,
                    "force_rlib": true
                }
            },
            "variants": [
                {},
                {
                    "tests": false,
                    "features": ["feature"],
                    "vendor_available": false,
                    "package": {
                        "another": {
                            "alloc": false,
                            "force_rlib": false
                        },
                        "variant_package": {
                            "add_module_block": "variant_module_block.bp"
                        }
                    }
                }
            ]
        }"#,
        )
        .unwrap();

        assert_eq!(
            config,
            Config {
                variants: vec![
                    VariantConfig {
                        tests: true,
                        features: None,
                        vendor_available: true,
                        package: [
                            ("argh".to_string(), PackageVariantConfig { ..Default::default() }),
                            (
                                "another".to_string(),
                                PackageVariantConfig {
                                    device_supported: false,
                                    force_rlib: true,
                                    ..Default::default()
                                },
                            ),
                        ]
                        .into_iter()
                        .collect(),
                        ..Default::default()
                    },
                    VariantConfig {
                        tests: false,
                        features: Some(vec!["feature".to_string()]),
                        vendor_available: false,
                        package: [
                            ("argh".to_string(), PackageVariantConfig { ..Default::default() }),
                            (
                                "another".to_string(),
                                PackageVariantConfig {
                                    alloc: false,
                                    device_supported: false,
                                    force_rlib: false,
                                    ..Default::default()
                                },
                            ),
                            (
                                "variant_package".to_string(),
                                PackageVariantConfig {
                                    add_module_block: Some("variant_module_block.bp".into()),
                                    ..Default::default()
                                },
                            ),
                        ]
                        .into_iter()
                        .collect(),
                        ..Default::default()
                    },
                ],
                package: [
                    (
                        "argh".to_string(),
                        PackageConfig {
                            patch: Some("patches/Android.bp.patch".into()),
                            ..Default::default()
                        },
                    ),
                    (
                        "another".to_string(),
                        PackageConfig {
                            add_toplevel_block: Some("block.bp".into()),
                            ..Default::default()
                        },
                    ),
                ]
                .into_iter()
                .collect(),
            }
        );
    }
}
