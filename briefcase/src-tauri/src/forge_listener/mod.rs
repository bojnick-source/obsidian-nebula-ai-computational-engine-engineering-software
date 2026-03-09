/// Background task that subscribes to the FORGE ZMQ PUB socket and
/// auto-ingests files on every `vault_write` event.
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;

use chrono::Utc;
use serde::Deserialize;
use uuid::Uuid;
use zeromq::{Socket, SocketRecv, SubSocket};

use crate::error::BriefcaseError;
use crate::models::AssetRecord;
use crate::store::{metadata_db, ObjectStore};

// ── FORGE event schema mirror ────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct ForgeEvent {
    run_id: Option<String>,
    agent: Option<String>,
    event_type: String,
    meta: Option<serde_json::Value>,
}

// ── Public entry point ───────────────────────────────────────────────────────

/// Spawns the listener loop; returns immediately. The loop runs until
/// `active` is set to `false` or the Tauri runtime shuts down.
pub fn spawn(
    endpoint: String,
    db: Arc<Mutex<rusqlite::Connection>>,
    object_store: Arc<Mutex<ObjectStore>>,
    active: Arc<AtomicBool>,
    app_handle: tauri::AppHandle,
) {
    tauri::async_runtime::spawn(async move {
        run_loop(endpoint, db, object_store, active, app_handle).await;
    });
}

// ── Internal implementation ──────────────────────────────────────────────────

async fn run_loop(
    endpoint: String,
    db: Arc<Mutex<rusqlite::Connection>>,
    object_store: Arc<Mutex<ObjectStore>>,
    active: Arc<AtomicBool>,
    app_handle: tauri::AppHandle,
) {
    let mut backoff_secs: u64 = 2;

    while active.load(Ordering::Relaxed) {
        match connect_and_listen(&endpoint, &db, &object_store, &active, &app_handle).await {
            Ok(_) => {
                backoff_secs = 2; // clean disconnect; reset backoff
            }
            Err(e) => {
                eprintln!("[briefcase] FORGE listener error: {e}");
                if !active.load(Ordering::Relaxed) {
                    break;
                }
                tokio::time::sleep(Duration::from_secs(backoff_secs)).await;
                backoff_secs = (backoff_secs * 2).min(60);
            }
        }
    }

    eprintln!("[briefcase] FORGE listener stopped.");
}

async fn connect_and_listen(
    endpoint: &str,
    db: &Arc<Mutex<rusqlite::Connection>>,
    object_store: &Arc<Mutex<ObjectStore>>,
    active: &Arc<AtomicBool>,
    app_handle: &tauri::AppHandle,
) -> Result<(), BriefcaseError> {
    let mut socket = SubSocket::new();
    socket
        .connect(endpoint)
        .await
        .map_err(|e| BriefcaseError::ForgeListener { message: e.to_string() })?;
    socket
        .subscribe("")
        .await
        .map_err(|e| BriefcaseError::ForgeListener { message: e.to_string() })?;

    eprintln!("[briefcase] FORGE listener connected to {endpoint}");
    emit_status(app_handle, true);

    while active.load(Ordering::Relaxed) {
        let recv = tokio::time::timeout(Duration::from_secs(5), socket.recv()).await;

        match recv {
            Ok(Ok(zmq_msg)) => {
                if let Some(frame) = zmq_msg.get(0) {
                    let json_str = String::from_utf8_lossy(frame);
                    if let Ok(event) = serde_json::from_str::<ForgeEvent>(&json_str) {
                        if event.event_type == "vault_write" {
                            handle_vault_write(event, db, object_store, app_handle).await;
                        }
                    }
                }
            }
            Ok(Err(e)) => {
                emit_status(app_handle, false);
                return Err(BriefcaseError::ForgeListener { message: e.to_string() });
            }
            Err(_) => {} // 5-second timeout — poll `active` flag and continue
        }
    }

    emit_status(app_handle, false);
    Ok(())
}

async fn handle_vault_write(
    event: ForgeEvent,
    db: &Arc<Mutex<rusqlite::Connection>>,
    object_store: &Arc<Mutex<ObjectStore>>,
    app_handle: &tauri::AppHandle,
) {
    let meta = match event.meta {
        Some(m) => m,
        None => return,
    };

    // FORGE writes the vault-relative or absolute file path as meta["path"]
    let file_path = match meta.get("path").and_then(|v| v.as_str()) {
        Some(p) => p.to_string(),
        None => return,
    };

    let project = meta.get("project").and_then(|v| v.as_str()).map(String::from);
    let source_agent = event.agent.filter(|s| !s.is_empty());
    let pipeline_id = event.run_id.filter(|s| !s.is_empty());

    let path = std::path::Path::new(&file_path);
    if !path.exists() {
        eprintln!("[briefcase] FORGE vault_write: path not found: {file_path}");
        return;
    }

    // Ingest into object store (blocking I/O)
    let os = object_store.clone();
    let path_buf = path.to_path_buf();
    let ingest_result = tokio::task::spawn_blocking(move || {
        let store = os.lock().map_err(|_| BriefcaseError::ForgeListener {
            message: "object store lock poisoned".into(),
        })?;
        store.ingest(&path_buf)
    })
    .await;

    let (content_hash, _) = match ingest_result {
        Ok(Ok(result)) => result,
        Ok(Err(e)) => {
            eprintln!("[briefcase] FORGE ingest error: {e}");
            return;
        }
        Err(e) => {
            eprintln!("[briefcase] FORGE spawn_blocking panic: {e}");
            return;
        }
    };

    // Check for duplicate
    {
        let db = db.clone();
        let hash = content_hash.clone();
        let is_dup = tokio::task::spawn_blocking(move || {
            let conn = db.lock().map_err(|_| BriefcaseError::ForgeListener {
                message: "db lock poisoned".into(),
            })?;
            metadata_db::find_by_hash(&conn, &hash)
        })
        .await;
        if let Ok(Ok(Some(_))) = is_dup {
            return; // already ingested
        }
    }

    let mime = mime_guess::from_path(path).first_or_octet_stream().to_string();
    let original_name = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown")
        .to_string();
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

    let now = Utc::now().to_rfc3339();
    let asset = AssetRecord {
        id: Uuid::new_v4().to_string(),
        content_hash,
        title,
        file_type: mime,
        original_name,
        project,
        subproject: None,
        source_agent,
        pipeline_id,
        importance: Default::default(),
        audience: Default::default(),
        confidentiality: Default::default(),
        vetted_status: Default::default(),
        tags: Vec::new(),
        classification_confidence: 0.0,
        classification_explanation: "auto-ingested via FORGE vault_write".to_string(),
        created_at: now.clone(),
        ingested_at: now,
        version: 1,
        superseded_by: None,
    };

    let db2 = db.clone();
    let asset_clone = asset.clone();
    let insert_result = tokio::task::spawn_blocking(move || {
        let conn = db2.lock().map_err(|_| BriefcaseError::ForgeListener {
            message: "db lock poisoned".into(),
        })?;
        metadata_db::insert_asset(&conn, &asset_clone)
    })
    .await;

    match insert_result {
        Ok(Ok(_)) => {
            let _ = app_handle.emit("forge://asset-ingested", &asset);
            eprintln!("[briefcase] FORGE auto-ingested: {}", asset.original_name);
        }
        Ok(Err(e)) => eprintln!("[briefcase] FORGE DB insert error: {e}"),
        Err(e) => eprintln!("[briefcase] FORGE spawn_blocking panic: {e}"),
    }
}

fn emit_status(app_handle: &tauri::AppHandle, connected: bool) {
    let _ = app_handle.emit("forge://listener-status", connected);
}
