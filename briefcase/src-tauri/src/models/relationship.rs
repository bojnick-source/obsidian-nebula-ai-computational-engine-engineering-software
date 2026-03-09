use serde::{Deserialize, Serialize};
use super::enums::RelationshipType;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AssetRelationship {
    pub source_id: String,
    pub target_id: String,
    pub relationship_type: RelationshipType,
    pub created_at: String,
}
