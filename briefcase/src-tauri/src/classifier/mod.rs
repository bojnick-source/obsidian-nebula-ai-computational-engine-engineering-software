/// LLM-based asset classifier using the Claude API.
///
/// Accepts an `AssetRecord` (after heuristic ingestion) and returns an
/// enriched copy with updated title, tags, importance, audience,
/// classification_confidence, and classification_explanation.
use serde::{Deserialize, Serialize};

use crate::error::BriefcaseError;
use crate::models::{AssetRecord, Audience, Importance};

const ANTHROPIC_API_URL: &str = "https://api.anthropic.com/v1/messages";
const MODEL: &str = "claude-haiku-4-5-20251001";
const MAX_TOKENS: u32 = 512;

// ── Request / response shapes ────────────────────────────────────────────────

#[derive(Serialize)]
struct Message {
    role: &'static str,
    content: String,
}

#[derive(Serialize)]
struct ClassifyRequest {
    model: &'static str,
    max_tokens: u32,
    system: String,
    messages: Vec<Message>,
}

#[derive(Deserialize)]
struct ApiResponse {
    content: Vec<ContentBlock>,
}

#[derive(Deserialize)]
struct ContentBlock {
    text: String,
}

/// The structured JSON the LLM returns inside the response text.
#[derive(Deserialize)]
struct Classification {
    title: Option<String>,
    tags: Option<Vec<String>>,
    importance: Option<String>,
    audience: Option<String>,
    confidence: Option<f64>,
    explanation: Option<String>,
}

// ── Public API ───────────────────────────────────────────────────────────────

/// Calls the Claude API to classify `asset` and returns an enriched copy.
/// On API failure, returns the original asset unchanged (fail-open).
pub async fn classify(asset: &AssetRecord, api_key: &str) -> AssetRecord {
    match run_classification(asset, api_key).await {
        Ok(updated) => updated,
        Err(e) => {
            eprintln!("[briefcase] LLM classification failed: {e}");
            asset.clone()
        }
    }
}

async fn run_classification(
    asset: &AssetRecord,
    api_key: &str,
) -> Result<AssetRecord, BriefcaseError> {
    let system = "You are a document classifier for an engineering output repository. \
        Respond ONLY with valid JSON — no markdown fences, no prose. \
        The JSON must have these keys: title (string), tags (array of strings, max 8), \
        importance (one of: critical, executive, technical, research, approved, archived), \
        audience (one of: executive, engineering, client, internal, public), \
        confidence (float 0-1), explanation (string, ≤ 120 chars).";

    let user_prompt = build_prompt(asset);

    let request_body = ClassifyRequest {
        model: MODEL,
        max_tokens: MAX_TOKENS,
        system: system.to_string(),
        messages: vec![Message {
            role: "user",
            content: user_prompt,
        }],
    };

    let client = reqwest::Client::new();
    let resp = client
        .post(ANTHROPIC_API_URL)
        .header("x-api-key", api_key)
        .header("anthropic-version", "2023-06-01")
        .header("content-type", "application/json")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| BriefcaseError::LlmClassifier { message: e.to_string() })?;

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().await.unwrap_or_default();
        return Err(BriefcaseError::LlmClassifier {
            message: format!("API {status}: {body}"),
        });
    }

    let api_resp: ApiResponse = resp
        .json()
        .await
        .map_err(|e| BriefcaseError::LlmClassifier { message: e.to_string() })?;

    let text = api_resp
        .content
        .into_iter()
        .next()
        .map(|b| b.text)
        .unwrap_or_default();

    let classification: Classification = serde_json::from_str(&text)
        .map_err(|e| BriefcaseError::LlmClassifier {
            message: format!("JSON parse error: {e} — raw: {text}"),
        })?;

    Ok(apply_classification(asset, classification))
}

fn build_prompt(asset: &AssetRecord) -> String {
    let mut parts = vec![
        format!("Filename: {}", asset.original_name),
        format!("MIME type: {}", asset.file_type),
    ];
    if let Some(ref project) = asset.project {
        parts.push(format!("Project: {project}"));
    }
    if !asset.tags.is_empty() {
        parts.push(format!("Existing tags: {}", asset.tags.join(", ")));
    }
    if let Some(ref agent) = asset.source_agent {
        parts.push(format!("Source agent: {agent}"));
    }
    parts.join("\n")
}

fn apply_classification(asset: &AssetRecord, c: Classification) -> AssetRecord {
    let mut updated = asset.clone();

    if let Some(title) = c.title {
        if !title.trim().is_empty() {
            updated.title = title;
        }
    }
    if let Some(tags) = c.tags {
        updated.tags = tags;
    }
    if let Some(imp_str) = c.importance {
        if let Ok(imp) = imp_str.parse::<Importance>() {
            updated.importance = imp;
        }
    }
    if let Some(aud_str) = c.audience {
        if let Ok(aud) = aud_str.parse::<Audience>() {
            updated.audience = aud;
        }
    }
    if let Some(conf) = c.confidence {
        updated.classification_confidence = conf.clamp(0.0, 1.0);
    }
    if let Some(expl) = c.explanation {
        updated.classification_explanation = expl;
    }

    updated
}
