use std::path::Path;
use tauri::State;
use chrono::Utc;
use uuid::Uuid;
use crate::error::BriefcaseError;
use crate::models::AssetRecord;
use crate::state::AppState;
use crate::store::metadata_db;

#[tauri::command]
pub fn ingest_file(
    state: State<'_, AppState>,
    file_path: String,
) -> Result<AssetRecord, BriefcaseError> {
    let path = Path::new(&file_path);

    if !path.exists() {
        return Err(BriefcaseError::NotFound {
            id: file_path.clone(),
        });
    }

    // Detect MIME type
    let mime = mime_guess::from_path(path)
        .first_or_octet_stream()
        .to_string();

    let original_name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();

    // Ingest into content-addressed object store
    let (content_hash, _was_duplicate) = {
        let store = state.object_store.lock().map_err(|_| {
            BriefcaseError::ObjectStore {
                message: "Failed to acquire object store lock".to_string(),
            }
        })?;
        store.ingest(path)?
    };

    let now = Utc::now().to_rfc3339();
    let id = Uuid::new_v4().to_string();

    // Derive a display title from filename (strip extension)
    let title = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or(&original_name)
        .replace(['-', '_'], " ")
        .split_whitespace()
        .map(|w| {
            let mut c = w.chars();
            match c.next() {
                None => String::new(),
                Some(f) => f.to_uppercase().collect::<String>() + c.as_str(),
            }
        })
        .collect::<Vec<_>>()
        .join(" ");

    let asset = AssetRecord {
        id,
        content_hash,
        title,
        file_type: mime,
        original_name,
        project: None,
        subproject: None,
        source_agent: None,
        pipeline_id: None,
        importance: Default::default(),
        audience: Default::default(),
        confidentiality: Default::default(),
        vetted_status: Default::default(),
        tags: Vec::new(),
        classification_confidence: 0.0,
        classification_explanation: String::new(),
        created_at: now.clone(),
        ingested_at: now,
        version: 1,
        superseded_by: None,
    };

    {
        let db = state.db.lock().map_err(|_| {
            BriefcaseError::ObjectStore {
                message: "Failed to acquire db lock".to_string(),
            }
        })?;
        metadata_db::insert_asset(&db, &asset)?;
    }

    Ok(asset)
}
