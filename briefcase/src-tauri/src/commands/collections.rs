use tauri::State;
use uuid::Uuid;
use chrono::Utc;

use crate::error::BriefcaseError;
use crate::models::collection::{Collection, CollectionItem};
use crate::state::AppState;
use crate::store::metadata_db;

// ── CRUD ─────────────────────────────────────────────────────────────────────

#[tauri::command]
pub fn create_collection(
    state: State<'_, AppState>,
    name: String,
    description: String,
) -> Result<Collection, BriefcaseError> {
    let now = Utc::now().to_rfc3339();
    let collection = Collection {
        id: Uuid::new_v4().to_string(),
        name,
        description,
        cover_asset_id: None,
        created_at: now.clone(),
        updated_at: now,
        item_count: 0,
    };
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::insert_collection(&db, &collection)?;
    Ok(collection)
}

#[tauri::command]
pub fn update_collection(
    state: State<'_, AppState>,
    id: String,
    name: String,
    description: String,
    cover_asset_id: Option<String>,
) -> Result<Collection, BriefcaseError> {
    let now = Utc::now().to_rfc3339();
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::update_collection(&db, &id, &name, &description, cover_asset_id.as_deref(), &now)?;
    metadata_db::get_collection(&db, &id)
}

#[tauri::command]
pub fn delete_collection(
    state: State<'_, AppState>,
    id: String,
) -> Result<(), BriefcaseError> {
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::delete_collection(&db, &id)
}

#[tauri::command]
pub fn list_collections(
    state: State<'_, AppState>,
) -> Result<Vec<Collection>, BriefcaseError> {
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::list_collections(&db)
}

// ── Items ─────────────────────────────────────────────────────────────────────

#[tauri::command]
pub fn get_collection_items(
    state: State<'_, AppState>,
    collection_id: String,
) -> Result<Vec<CollectionItem>, BriefcaseError> {
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::get_collection_items(&db, &collection_id)
}

#[tauri::command]
pub fn add_to_collection(
    state: State<'_, AppState>,
    collection_id: String,
    asset_id: String,
    slide_notes: String,
) -> Result<(), BriefcaseError> {
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::add_to_collection(&db, &collection_id, &asset_id, &slide_notes)
}

#[tauri::command]
pub fn remove_from_collection(
    state: State<'_, AppState>,
    collection_id: String,
    asset_id: String,
) -> Result<(), BriefcaseError> {
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::remove_from_collection(&db, &collection_id, &asset_id)
}

#[tauri::command]
pub fn reorder_collection_item(
    state: State<'_, AppState>,
    collection_id: String,
    asset_id: String,
    position: i64,
) -> Result<(), BriefcaseError> {
    let db = state.db.lock().map_err(|_| db_lock_err())?;
    metadata_db::reorder_collection_item(&db, &collection_id, &asset_id, position)
}

fn db_lock_err() -> BriefcaseError {
    BriefcaseError::ObjectStore { message: "Failed to acquire db lock".to_string() }
}
