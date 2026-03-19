use tauri::State;
use crate::error::BriefcaseError;
use crate::models::AssetRelationship;
use crate::state::AppState;
use crate::store::metadata_db;

#[tauri::command]
pub fn get_relationships(
    state: State<'_, AppState>,
    asset_id: String,
) -> Result<Vec<AssetRelationship>, BriefcaseError> {
    let db = state.db.lock().map_err(|_| BriefcaseError::LockPoisoned {
        context: "AppState.db mutex poisoned".to_string(),
    })?;
    metadata_db::get_relationships(&db, &asset_id)
}
