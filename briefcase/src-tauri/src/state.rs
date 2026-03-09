use rusqlite::Connection;
use std::sync::Mutex;
use crate::store::ObjectStore;

pub struct AppState {
    pub object_store: Mutex<ObjectStore>,
    pub db: Mutex<Connection>,
}
