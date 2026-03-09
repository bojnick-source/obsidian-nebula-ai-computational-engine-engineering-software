use serde::{Deserialize, Serialize};
use super::enums::{Audience, Confidentiality, Importance, VettedStatus};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AssetRecord {
    pub id: String,
    pub content_hash: String,
    pub title: String,
    pub file_type: String,
    pub original_name: String,
    pub project: Option<String>,
    pub subproject: Option<String>,
    pub source_agent: Option<String>,
    pub pipeline_id: Option<String>,
    pub importance: Importance,
    pub audience: Audience,
    pub confidentiality: Confidentiality,
    pub vetted_status: VettedStatus,
    pub tags: Vec<String>,
    pub classification_confidence: f64,
    pub classification_explanation: String,
    pub created_at: String,
    pub ingested_at: String,
    pub version: i64,
    pub superseded_by: Option<String>,
}

impl AssetRecord {
    pub fn tags_json(&self) -> String {
        serde_json::to_string(&self.tags).unwrap_or_else(|_| "[]".to_string())
    }
}
