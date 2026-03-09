use tauri::State;

use crate::classifier;
use crate::error::BriefcaseError;
use crate::models::AssetRecord;
use crate::state::AppState;
use crate::store::metadata_db;

/// Classify an existing asset with the LLM and persist the enriched metadata.
///
/// If `api_key` is provided it overrides the key stored in `AppState`.
/// On classification failure the original asset is returned unchanged.
#[tauri::command]
pub async fn classify_asset(
    state: State<'_, AppState>,
    id: String,
    api_key: Option<String>,
) -> Result<AssetRecord, BriefcaseError> {
    // Resolve API key: explicit arg > stored key
    let key = {
        let key_arg = api_key.filter(|k| !k.is_empty());
        let stored = state.api_key.lock().map_err(|_| BriefcaseError::LlmClassifier {
            message: "api_key lock poisoned".to_string(),
        })?;
        key_arg.or_else(|| stored.clone())
    };

    let key = match key {
        Some(k) => k,
        None => {
            return Err(BriefcaseError::LlmClassifier {
                message: "No Claude API key configured. Call set_api_key first.".to_string(),
            })
        }
    };

    // Fetch asset from DB (blocking)
    let db_arc = state.db.clone();
    let id2 = id.clone();
    let asset = tokio::task::spawn_blocking(move || {
        let conn = db_arc.lock().map_err(|_| BriefcaseError::ObjectStore {
            message: "db lock poisoned".to_string(),
        })?;
        metadata_db::get_asset(&conn, &id2)
    })
    .await
    .map_err(|e| BriefcaseError::LlmClassifier { message: e.to_string() })??;

    // Call Claude API
    let enriched = classifier::classify(&asset, &key).await;

    // Persist updated fields
    let patch = crate::models::AssetPatch {
        title: Some(enriched.title.clone()),
        tags: Some(enriched.tags.clone()),
        importance: Some(enriched.importance.clone()),
        audience: Some(enriched.audience.clone()),
        confidentiality: None,
        vetted_status: Some(crate::models::VettedStatus::AiVetted),
        project: enriched.project.clone(),
        subproject: enriched.subproject.clone(),
        classification_explanation: Some(enriched.classification_explanation.clone()),
        superseded_by: None,
    };

    let db_arc2 = state.db.clone();
    let updated = tokio::task::spawn_blocking(move || {
        let conn = db_arc2.lock().map_err(|_| BriefcaseError::ObjectStore {
            message: "db lock poisoned".to_string(),
        })?;
        metadata_db::update_asset(&conn, &id, &patch)
    })
    .await
    .map_err(|e| BriefcaseError::LlmClassifier { message: e.to_string() })??;

    Ok(updated)
}
