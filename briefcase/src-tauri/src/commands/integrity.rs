use tauri::State;
use crate::error::BriefcaseError;
use crate::models::{AssetPatch, AssetRecord};
use crate::state::AppState;
use crate::store::metadata_db;

#[tauri::command]
pub fn verify_integrity(
    state: State<'_, AppState>,
    content_hash: String,
) -> Result<bool, BriefcaseError> {
    let store = state.object_store.lock().map_err(|_| BriefcaseError::ObjectStore {
        message: "store lock failed".to_string(),
    })?;
    store.verify(&content_hash)
}

#[tauri::command]
pub fn update_asset_metadata(
    state: State<'_, AppState>,
    id: String,
    patch: AssetPatch,
) -> Result<AssetRecord, BriefcaseError> {
    let db = state.db.lock().map_err(|_| BriefcaseError::ObjectStore {
        message: "db lock failed".to_string(),
    })?;
    metadata_db::update_asset(&db, &id, &patch)
}
