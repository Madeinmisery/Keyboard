use core::fmt::Display;
use std::path::{Path, PathBuf};

#[derive(Debug, PartialEq, Eq)]
pub struct RepoPath {
    root: PathBuf,
    path: PathBuf,
}

impl Display for RepoPath {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.path.display())
    }
}

impl RepoPath {
    pub fn new<P: Into<PathBuf>, Q: Into<PathBuf>>(root: P, path: Q) -> RepoPath {
        let root: PathBuf = root.into();
        let path: PathBuf = path.into();
        assert!(root.is_absolute());
        assert!(path.is_relative());
        RepoPath { root, path }
    }
    pub fn root(&self) -> &Path {
        self.root.as_path()
    }
    pub fn rel(&self) -> &Path {
        self.path.as_path()
    }
    pub fn abs(&self) -> PathBuf {
        self.root.join(&self.path)
    }
    pub fn join(&self, path: &impl AsRef<Path>) -> RepoPath {
        RepoPath::new(self.root.clone(), self.path.join(path))
    }
    pub fn with_same_root<P: Into<PathBuf>>(&self, path: P) -> RepoPath {
        RepoPath::new(self.root.clone(), path)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic() {
        let p = RepoPath::new(&"/foo", &"bar");
        assert_eq!(p.root(), Path::new("/foo"));
        assert_eq!(p.rel(), Path::new("bar"));
        assert_eq!(p.abs(), PathBuf::from("/foo/bar"));
        assert_eq!(p.join(&"baz"), RepoPath::new("/foo", "bar/baz"));
        assert_eq!(p.with_same_root(&"baz"), RepoPath::new("/foo", "baz"));
    }
}
