use serde::{Deserialize, Serialize};
use super::enums::{Audience, Confidentiality, Importance, VettedStatus};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct AssetFilter {
    pub project: Option<String>,
    pub importance: Option<Importance>,
    pub audience: Option<Audience>,
    pub confidentiality: Option<Confidentiality>,
    pub vetted_status: Option<VettedStatus>,
    pub file_type: Option<String>,
    pub tag: Option<String>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct AssetPatch {
    pub title: Option<String>,
    pub project: Option<String>,
    pub subproject: Option<String>,
    pub importance: Option<Importance>,
    pub audience: Option<Audience>,
    pub confidentiality: Option<Confidentiality>,
    pub vetted_status: Option<VettedStatus>,
    pub tags: Option<Vec<String>>,
    pub classification_explanation: Option<String>,
    pub superseded_by: Option<String>,
}
