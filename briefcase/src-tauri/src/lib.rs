pub mod classifier;
pub mod commands;
pub mod error;
pub mod forge_listener;
pub mod models;
pub mod state;
pub mod store;

use std::sync::atomic::AtomicBool;
use std::sync::{Arc, Mutex};

use rusqlite::Connection;
use tauri::Manager;

use state::AppState;
use store::{initialize_collections_schema, initialize_schema, ObjectStore};

// Import all commands — generate_handler! requires functions in scope
use commands::classify::classify_asset;
use commands::collections::{
    add_to_collection, create_collection, delete_collection, get_collection_items,
    list_collections, remove_from_collection, reorder_collection_item, update_collection,
};
use commands::forge::{
    get_api_key_status, get_forge_listener_status, set_api_key, start_forge_listener,
    stop_forge_listener,
};
use commands::ingest::ingest_file;
use commands::integrity::{update_asset_metadata, verify_integrity};
use commands::query::{get_asset, list_assets, search_assets};
use commands::relationships::get_relationships;
use commands::serve::get_file_url;

fn get_data_dir(app: &tauri::App) -> std::path::PathBuf {
    app.path()
        .app_data_dir()
        .unwrap_or_else(|_| std::path::PathBuf::from("."))
        .join("briefcase")
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .setup(|app| {
            let data_dir = get_data_dir(app);
            std::fs::create_dir_all(&data_dir)?;

            let object_store = ObjectStore::new(data_dir.clone())
                .expect("Failed to initialize object store");

            let db_path = data_dir.join("briefcase.db");
            let db = Connection::open(&db_path)
                .expect("Failed to open SQLite database");
            initialize_schema(&db).expect("Failed to initialize database schema");
            initialize_collections_schema(&db).expect("Failed to initialize collections schema");

            app.manage(AppState {
                object_store: Arc::new(Mutex::new(object_store)),
                db: Arc::new(Mutex::new(db)),
                forge_active: Arc::new(AtomicBool::new(false)),
                api_key: Arc::new(Mutex::new(None)),
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Phase 1 commands
            ingest_file,
            get_asset,
            list_assets,
            search_assets,
            get_relationships,
            get_file_url,
            verify_integrity,
            update_asset_metadata,
            // Phase 2 — FORGE listener & LLM
            start_forge_listener,
            stop_forge_listener,
            get_forge_listener_status,
            set_api_key,
            get_api_key_status,
            classify_asset,
            // Phase 2 — Collections
            create_collection,
            update_collection,
            delete_collection,
            list_collections,
            get_collection_items,
            add_to_collection,
            remove_from_collection,
            reorder_collection_item,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Briefcase");
}
