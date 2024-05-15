use std::{
    ffi::OsString,
    fs::{create_dir_all, remove_dir_all, remove_file},
    path::PathBuf,
};

use anyhow::{anyhow, Context, Result};
use clap::{Parser, Subcommand};
use copy_dir::copy_dir;
use external_crates::default_repo_root;

#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    command: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    Migrate { crate_name: String },
    Check { files: Vec<String> },
}

fn main() -> Result<()> {
    let args = Cli::parse();
    match args.command {
        Cmd::Migrate { crate_name } => {
            let repo_root = default_repo_root()?;
            let old_path = PathBuf::from("external/rust/crates").join(&crate_name);
            if !repo_root.join(&old_path).is_dir() {
                return Err(anyhow!(
                    "Crate {} not found at {}",
                    crate_name,
                    old_path.display()
                ));
            }
            let new_root = PathBuf::from("external/rust/android-crates-io/crates");
            if !repo_root.join(&new_root).is_dir() {
                create_dir_all(repo_root.join(&new_root))
                    .context(format!("Failed to create dir {}", new_root.display()))?;
            }
            let new_path = new_root.join(crate_name);
            if repo_root.join(&new_path).is_dir() {
                remove_dir_all(repo_root.join(&new_path))
                    .context(format!("Failed to remove dir {}", new_path.display()))?;
            }
            copy_dir(repo_root.join(&old_path), repo_root.join(&new_path)).context(format!(
                "Failed to copy {} to {}",
                old_path.display(),
                new_path.display()
            ))?;
            let test_mapping = old_path.join("TEST_MAPPING");
            if repo_root.join(&test_mapping).exists() {
                remove_file(repo_root.join(&test_mapping))
                    .context(format!("Failed to remove {}", test_mapping.display()))?;
            }
            for dir_entry in repo_root.join(&old_path).read_dir()? {
                let bp: PathBuf = old_path.join(dir_entry?.file_name());
                if bp
                    .extension()
                    .is_some_and(|extension| extension == OsString::from("bp"))
                {
                    remove_file(repo_root.join(&bp))
                        .context(format!("Failed to remove {}", bp.display()))?;
                }
            }
            Ok(())
        }
        Cmd::Check { files } => {
            for file in files {
                println!("{}", file)
            }
            Ok(())
        }
    }
}
