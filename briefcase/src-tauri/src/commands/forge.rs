use std::sync::atomic::Ordering;
use tauri::State;

use crate::error::BriefcaseError;
use crate::forge_listener;
use crate::state::AppState;

/// Store the Claude API key in memory for the lifetime of the session.
/// The key is never written to disk.
#[tauri::command]
pub fn set_api_key(state: State<'_, AppState>, api_key: String) -> Result<(), BriefcaseError> {
    let mut key = state.api_key.lock().map_err(|_| BriefcaseError::ObjectStore {
        message: "api_key lock poisoned".to_string(),
    })?;
    *key = if api_key.is_empty() { None } else { Some(api_key) };
    Ok(())
}

/// Returns whether a Claude API key is currently stored.
#[tauri::command]
pub fn get_api_key_status(state: State<'_, AppState>) -> bool {
    state
        .api_key
        .lock()
        .map(|k| k.is_some())
        .unwrap_or(false)
}

/// Start the FORGE ZMQ listener on the given endpoint.
/// Defaults to `tcp://127.0.0.1:5555` if not provided.
#[tauri::command]
pub fn start_forge_listener(
    state: State<'_, AppState>,
    app_handle: tauri::AppHandle,
    endpoint: Option<String>,
) -> Result<(), BriefcaseError> {
    if state.forge_active.load(Ordering::Relaxed) {
        return Ok(()); // already running
    }

    let ep = endpoint.unwrap_or_else(|| "tcp://127.0.0.1:5555".to_string());
    state.forge_active.store(true, Ordering::Relaxed);

    forge_listener::spawn(
        ep,
        state.db.clone(),
        state.object_store.clone(),
        state.forge_active.clone(),
        app_handle,
    );

    Ok(())
}

/// Stop the FORGE ZMQ listener. The current connection is closed at the next
/// poll interval (≤ 5 seconds).
#[tauri::command]
pub fn stop_forge_listener(state: State<'_, AppState>) -> Result<(), BriefcaseError> {
    state.forge_active.store(false, Ordering::Relaxed);
    Ok(())
}

/// Returns `true` when the listener task is running.
#[tauri::command]
pub fn get_forge_listener_status(state: State<'_, AppState>) -> bool {
    state.forge_active.load(Ordering::Relaxed)
}
