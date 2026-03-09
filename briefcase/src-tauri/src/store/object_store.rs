use std::path::{Path, PathBuf};
use sha2::{Digest, Sha256};
use std::io::Read;
use crate::error::BriefcaseError;

pub struct ObjectStore {
    root: PathBuf,
}

impl ObjectStore {
    pub fn new(root: PathBuf) -> Result<Self, BriefcaseError> {
        std::fs::create_dir_all(&root)?;
        Ok(ObjectStore { root })
    }

    /// Compute the SHA-256 hash of a file, reading in chunks to support large files.
    pub fn hash_file(path: &Path) -> Result<String, BriefcaseError> {
        let mut file = std::fs::File::open(path)?;
        let mut hasher = Sha256::new();
        let mut buf = vec![0u8; 64 * 1024]; // 64 KB chunks
        loop {
            let n = file.read(&mut buf)?;
            if n == 0 {
                break;
            }
            hasher.update(&buf[..n]);
        }
        Ok(hex::encode(hasher.finalize()))
    }

    /// Ingest a file into the content-addressed object store.
    /// Returns (content_hash, was_duplicate).
    pub fn ingest(&self, source: &Path) -> Result<(String, bool), BriefcaseError> {
        let hash = Self::hash_file(source)?;
        let dest = self.object_path(&hash);

        if dest.exists() {
            return Ok((hash, true));
        }

        if let Some(parent) = dest.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::copy(source, &dest)?;
        Ok((hash, false))
    }

    /// Get the filesystem path for a stored object by its content hash.
    pub fn retrieve_path(&self, hash: &str) -> Result<PathBuf, BriefcaseError> {
        let path = self.object_path(hash);
        if path.exists() {
            Ok(path)
        } else {
            Err(BriefcaseError::NotFound {
                id: hash.to_string(),
            })
        }
    }

    /// Verify integrity by re-hashing the stored file and comparing to its address.
    pub fn verify(&self, hash: &str) -> Result<bool, BriefcaseError> {
        let path = self.object_path(hash);
        if !path.exists() {
            return Ok(false);
        }
        let actual = Self::hash_file(&path)?;
        Ok(actual == hash)
    }

    /// Compute the sharded storage path for a hash.
    /// Layout: objects/{hash[0..2]}/{hash[2..4]}/{hash}
    fn object_path(&self, hash: &str) -> PathBuf {
        if hash.len() < 4 {
            return self.root.join("objects").join(hash);
        }
        self.root
            .join("objects")
            .join(&hash[0..2])
            .join(&hash[2..4])
            .join(hash)
    }
}
