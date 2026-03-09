use tauri::State;
use crate::error::BriefcaseError;
use crate::state::AppState;

#[tauri::command]
pub fn get_file_url(
    state: State<'_, AppState>,
    content_hash: String,
) -> Result<String, BriefcaseError> {
    // Verify the file exists in the object store
    let store = state.object_store.lock().map_err(|_| BriefcaseError::ObjectStore {
        message: "store lock failed".to_string(),
    })?;
    let path = store.retrieve_path(&content_hash)?;
    // Return the absolute path as a string; the frontend converts this to a
    // convertFileSrc() URL using the Tauri asset protocol.
    Ok(path.to_string_lossy().to_string())
}
