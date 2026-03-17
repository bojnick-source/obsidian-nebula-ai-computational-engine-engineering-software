use tauri::State;
use crate::error::BriefcaseError;
use crate::models::{AssetFilter, AssetRecord};
use crate::state::AppState;
use crate::store::metadata_db;

#[tauri::command]
pub fn get_asset(
    state: State<'_, AppState>,
    id: String,
) -> Result<AssetRecord, BriefcaseError> {
    let db = state.db.lock().map_err(|_| BriefcaseError::LockPoisoned {
        context: "AppState.db mutex poisoned".to_string(),
    })?;
    metadata_db::get_asset(&db, &id)
}

#[tauri::command]
pub fn list_assets(
    state: State<'_, AppState>,
    filter: AssetFilter,
) -> Result<Vec<AssetRecord>, BriefcaseError> {
    let db = state.db.lock().map_err(|_| BriefcaseError::LockPoisoned {
        context: "AppState.db mutex poisoned".to_string(),
    })?;
    metadata_db::list_assets(&db, &filter)
}

#[tauri::command]
pub fn search_assets(
    state: State<'_, AppState>,
    query: String,
) -> Result<Vec<AssetRecord>, BriefcaseError> {
    let db = state.db.lock().map_err(|_| BriefcaseError::LockPoisoned {
        context: "AppState.db mutex poisoned".to_string(),
    })?;
    metadata_db::search_assets(&db, &query)
}
