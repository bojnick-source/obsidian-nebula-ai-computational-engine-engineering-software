use thiserror::Error;

#[derive(Debug, Error)]
pub enum BriefcaseError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),

    #[error("Hash mismatch: expected {expected}, got {actual}")]
    IntegrityFailure { expected: String, actual: String },

    #[error("Asset not found: {id}")]
    NotFound { id: String },

    #[error("MIME detection failed for path: {path}")]
    MimeDetection { path: String },

    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),

    #[error("UUID parse error: {0}")]
    UuidParse(#[from] uuid::Error),

    #[error("Invalid enum value: {value}")]
    InvalidEnum { value: String },

    #[error("Object store error: {message}")]
    ObjectStore { message: String },

    #[error("Internal lock poisoned: {context}")]
    LockPoisoned { context: String },

    #[error("FORGE listener error: {message}")]
    ForgeListener { message: String },

    #[error("LLM classifier error: {message}")]
    LlmClassifier { message: String },
}

// Required for Tauri IPC: serializes errors as JSON strings to the frontend
impl serde::Serialize for BriefcaseError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::ser::Serializer,
    {
        serializer.serialize_str(self.to_string().as_ref())
    }
}
