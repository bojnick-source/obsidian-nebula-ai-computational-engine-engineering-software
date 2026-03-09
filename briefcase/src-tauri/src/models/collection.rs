use serde::{Deserialize, Serialize};

/// A named, ordered collection of assets — the unit of a Presentation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Collection {
    pub id: String,
    pub name: String,
    pub description: String,
    pub cover_asset_id: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    /// Denormalized count, computed at query time.
    pub item_count: i64,
}

/// A single slot in an ordered collection — carries per-slide presenter notes.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CollectionItem {
    pub collection_id: String,
    pub asset_id: String,
    pub position: i64,
    pub slide_notes: String,
}
