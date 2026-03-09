pub mod commands;
pub mod error;
pub mod models;
pub mod state;
pub mod store;

use rusqlite::Connection;
use std::path::PathBuf;
use tauri::Manager;
use state::AppState;
use store::{initialize_schema, ObjectStore};

// Import all commands directly — generate_handler! requires functions in scope
use commands::ingest::ingest_file;
use commands::integrity::{update_asset_metadata, verify_integrity};
use commands::query::{get_asset, list_assets, search_assets};
use commands::relationships::get_relationships;
use commands::serve::get_file_url;

fn get_data_dir(app: &tauri::App) -> PathBuf {
    app.path()
        .app_data_dir()
        .unwrap_or_else(|_| PathBuf::from("."))
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

            app.manage(AppState {
                object_store: std::sync::Mutex::new(object_store),
                db: std::sync::Mutex::new(db),
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            ingest_file,
            get_asset,
            list_assets,
            search_assets,
            get_relationships,
            get_file_url,
            verify_integrity,
            update_asset_metadata,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Briefcase");
}
