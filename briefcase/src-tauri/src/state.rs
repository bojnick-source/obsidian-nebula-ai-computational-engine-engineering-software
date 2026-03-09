use rusqlite::Connection;
use std::sync::atomic::AtomicBool;
use std::sync::{Arc, Mutex};
use crate::store::ObjectStore;

pub struct AppState {
    /// Content-addressed file store. Wrapped in Arc so the FORGE listener
    /// task can hold a clone across await points.
    pub object_store: Arc<Mutex<ObjectStore>>,

    /// SQLite connection. Wrapped in Arc for the same reason.
    pub db: Arc<Mutex<Connection>>,

    /// Signals the FORGE listener task to keep running (true) or stop (false).
    pub forge_active: Arc<AtomicBool>,

    /// Claude API key, stored in memory only — never persisted to disk.
    pub api_key: Arc<Mutex<Option<String>>>,
}
