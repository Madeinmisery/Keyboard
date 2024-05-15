use std::env::current_dir;
use std::path::PathBuf;

use anyhow::{anyhow, Context, Result};

pub fn default_repo_root() -> Result<PathBuf> {
    let cwd = current_dir().context("Could not get current working directory")?;
    for cur in cwd.ancestors() {
        for e in cur.read_dir()? {
            if e?.file_name() == ".repo" {
                return Ok(cur.to_path_buf());
            }
        }
    }
    Err(anyhow!(
        ".repo directory not found in any ancestor of {}",
        cwd.display()
    ))
}
