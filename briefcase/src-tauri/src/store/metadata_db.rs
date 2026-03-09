use rusqlite::{Connection, params};
use std::str::FromStr;
use crate::error::BriefcaseError;
use crate::models::{AssetFilter, AssetPatch, AssetRecord, AssetRelationship, RelationshipType};
use crate::models::enums::{Audience, Confidentiality, Importance, VettedStatus};

/// Initialize the SQLite database schema on first connection.
pub fn initialize_schema(conn: &Connection) -> Result<(), BriefcaseError> {
    conn.execute_batch(
        r#"
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;

        CREATE TABLE IF NOT EXISTS assets (
            id                         TEXT PRIMARY KEY,
            content_hash               TEXT NOT NULL,
            title                      TEXT NOT NULL,
            file_type                  TEXT NOT NULL,
            original_name              TEXT NOT NULL,
            project                    TEXT,
            subproject                 TEXT,
            source_agent               TEXT,
            pipeline_id                TEXT,
            importance                 TEXT NOT NULL DEFAULT 'technical',
            audience                   TEXT NOT NULL DEFAULT 'internal',
            confidentiality            TEXT NOT NULL DEFAULT 'internal',
            vetted_status              TEXT NOT NULL DEFAULT 'unvetted',
            tags                       TEXT NOT NULL DEFAULT '[]',
            classification_confidence  REAL NOT NULL DEFAULT 0.0,
            classification_explanation TEXT NOT NULL DEFAULT '',
            created_at                 TEXT NOT NULL,
            ingested_at                TEXT NOT NULL,
            version                    INTEGER NOT NULL DEFAULT 1,
            superseded_by              TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_assets_content_hash ON assets(content_hash);
        CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project);
        CREATE INDEX IF NOT EXISTS idx_assets_importance ON assets(importance);
        CREATE INDEX IF NOT EXISTS idx_assets_ingested_at ON assets(ingested_at DESC);

        CREATE VIRTUAL TABLE IF NOT EXISTS assets_fts
            USING fts5(
                title,
                original_name,
                tags,
                project,
                content='assets',
                content_rowid='rowid'
            );

        CREATE TRIGGER IF NOT EXISTS assets_fts_insert
            AFTER INSERT ON assets BEGIN
                INSERT INTO assets_fts(rowid, title, original_name, tags, project)
                VALUES (new.rowid, new.title, new.original_name, new.tags, COALESCE(new.project, ''));
            END;

        CREATE TRIGGER IF NOT EXISTS assets_fts_update
            AFTER UPDATE ON assets BEGIN
                INSERT INTO assets_fts(assets_fts, rowid, title, original_name, tags, project)
                VALUES ('delete', old.rowid, old.title, old.original_name, old.tags, COALESCE(old.project, ''));
                INSERT INTO assets_fts(rowid, title, original_name, tags, project)
                VALUES (new.rowid, new.title, new.original_name, new.tags, COALESCE(new.project, ''));
            END;

        CREATE TRIGGER IF NOT EXISTS assets_fts_delete
            AFTER DELETE ON assets BEGIN
                INSERT INTO assets_fts(assets_fts, rowid, title, original_name, tags, project)
                VALUES ('delete', old.rowid, old.title, old.original_name, old.tags, COALESCE(old.project, ''));
            END;

        CREATE TABLE IF NOT EXISTS asset_relationships (
            source_id         TEXT NOT NULL,
            target_id         TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            created_at        TEXT NOT NULL,
            PRIMARY KEY (source_id, target_id, relationship_type)
        );

        CREATE INDEX IF NOT EXISTS idx_rel_source ON asset_relationships(source_id);
        CREATE INDEX IF NOT EXISTS idx_rel_target ON asset_relationships(target_id);
        "#,
    )?;
    Ok(())
}

pub fn insert_asset(conn: &Connection, asset: &AssetRecord) -> Result<(), BriefcaseError> {
    conn.execute(
        r#"INSERT INTO assets (
            id, content_hash, title, file_type, original_name,
            project, subproject, source_agent, pipeline_id,
            importance, audience, confidentiality, vetted_status,
            tags, classification_confidence, classification_explanation,
            created_at, ingested_at, version, superseded_by
        ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,?16,?17,?18,?19,?20)"#,
        params![
            asset.id,
            asset.content_hash,
            asset.title,
            asset.file_type,
            asset.original_name,
            asset.project,
            asset.subproject,
            asset.source_agent,
            asset.pipeline_id,
            asset.importance.to_string(),
            asset.audience.to_string(),
            asset.confidentiality.to_string(),
            asset.vetted_status.to_string(),
            asset.tags_json(),
            asset.classification_confidence,
            asset.classification_explanation,
            asset.created_at,
            asset.ingested_at,
            asset.version,
            asset.superseded_by,
        ],
    )?;
    Ok(())
}

pub fn get_asset(conn: &Connection, id: &str) -> Result<AssetRecord, BriefcaseError> {
    let mut stmt = conn.prepare(
        "SELECT id, content_hash, title, file_type, original_name,
                project, subproject, source_agent, pipeline_id,
                importance, audience, confidentiality, vetted_status,
                tags, classification_confidence, classification_explanation,
                created_at, ingested_at, version, superseded_by
         FROM assets WHERE id = ?1",
    )?;
    let record = stmt.query_row(params![id], row_to_asset).map_err(|_| {
        BriefcaseError::NotFound {
            id: id.to_string(),
        }
    })?;
    Ok(record)
}

pub fn list_assets(
    conn: &Connection,
    filter: &AssetFilter,
) -> Result<Vec<AssetRecord>, BriefcaseError> {
    let mut conditions: Vec<String> = Vec::new();
    let mut param_values: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

    if let Some(project) = &filter.project {
        conditions.push(format!("project = ?{}", param_values.len() + 1));
        param_values.push(Box::new(project.clone()));
    }
    if let Some(importance) = &filter.importance {
        conditions.push(format!("importance = ?{}", param_values.len() + 1));
        param_values.push(Box::new(importance.to_string()));
    }
    if let Some(audience) = &filter.audience {
        conditions.push(format!("audience = ?{}", param_values.len() + 1));
        param_values.push(Box::new(audience.to_string()));
    }
    if let Some(confidentiality) = &filter.confidentiality {
        conditions.push(format!("confidentiality = ?{}", param_values.len() + 1));
        param_values.push(Box::new(confidentiality.to_string()));
    }
    if let Some(vetted_status) = &filter.vetted_status {
        conditions.push(format!("vetted_status = ?{}", param_values.len() + 1));
        param_values.push(Box::new(vetted_status.to_string()));
    }
    if let Some(file_type) = &filter.file_type {
        conditions.push(format!("file_type = ?{}", param_values.len() + 1));
        param_values.push(Box::new(file_type.clone()));
    }

    let where_clause = if conditions.is_empty() {
        String::new()
    } else {
        format!("WHERE {}", conditions.join(" AND "))
    };

    let limit = filter.limit.unwrap_or(500);
    let offset = filter.offset.unwrap_or(0);

    let sql = format!(
        "SELECT id, content_hash, title, file_type, original_name,
                project, subproject, source_agent, pipeline_id,
                importance, audience, confidentiality, vetted_status,
                tags, classification_confidence, classification_explanation,
                created_at, ingested_at, version, superseded_by
         FROM assets {where_clause}
         ORDER BY ingested_at DESC
         LIMIT {limit} OFFSET {offset}"
    );

    let mut stmt = conn.prepare(&sql)?;
    let params_refs: Vec<&dyn rusqlite::ToSql> = param_values.iter().map(|v| v.as_ref()).collect();
    let rows = stmt.query_map(params_refs.as_slice(), row_to_asset)?;
    let mut results = Vec::new();
    for row in rows {
        results.push(row?);
    }
    Ok(results)
}

pub fn search_assets(
    conn: &Connection,
    query: &str,
) -> Result<Vec<AssetRecord>, BriefcaseError> {
    if query.trim().is_empty() {
        return Ok(Vec::new());
    }
    let mut stmt = conn.prepare(
        r#"SELECT a.id, a.content_hash, a.title, a.file_type, a.original_name,
                  a.project, a.subproject, a.source_agent, a.pipeline_id,
                  a.importance, a.audience, a.confidentiality, a.vetted_status,
                  a.tags, a.classification_confidence, a.classification_explanation,
                  a.created_at, a.ingested_at, a.version, a.superseded_by
           FROM assets a
           JOIN assets_fts fts ON a.rowid = fts.rowid
           WHERE assets_fts MATCH ?1
           ORDER BY rank
           LIMIT 200"#,
    )?;
    let rows = stmt.query_map(params![query], row_to_asset)?;
    let mut results = Vec::new();
    for row in rows {
        results.push(row?);
    }
    Ok(results)
}

pub fn update_asset(
    conn: &Connection,
    id: &str,
    patch: &AssetPatch,
) -> Result<AssetRecord, BriefcaseError> {
    let mut sets: Vec<String> = Vec::new();
    let mut param_values: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

    if let Some(title) = &patch.title {
        sets.push(format!("title = ?{}", param_values.len() + 1));
        param_values.push(Box::new(title.clone()));
    }
    if let Some(project) = &patch.project {
        sets.push(format!("project = ?{}", param_values.len() + 1));
        param_values.push(Box::new(project.clone()));
    }
    if let Some(subproject) = &patch.subproject {
        sets.push(format!("subproject = ?{}", param_values.len() + 1));
        param_values.push(Box::new(subproject.clone()));
    }
    if let Some(importance) = &patch.importance {
        sets.push(format!("importance = ?{}", param_values.len() + 1));
        param_values.push(Box::new(importance.to_string()));
    }
    if let Some(audience) = &patch.audience {
        sets.push(format!("audience = ?{}", param_values.len() + 1));
        param_values.push(Box::new(audience.to_string()));
    }
    if let Some(confidentiality) = &patch.confidentiality {
        sets.push(format!("confidentiality = ?{}", param_values.len() + 1));
        param_values.push(Box::new(confidentiality.to_string()));
    }
    if let Some(vetted_status) = &patch.vetted_status {
        sets.push(format!("vetted_status = ?{}", param_values.len() + 1));
        param_values.push(Box::new(vetted_status.to_string()));
    }
    if let Some(tags) = &patch.tags {
        let tags_json = serde_json::to_string(tags)?;
        sets.push(format!("tags = ?{}", param_values.len() + 1));
        param_values.push(Box::new(tags_json));
    }
    if let Some(explanation) = &patch.classification_explanation {
        sets.push(format!("classification_explanation = ?{}", param_values.len() + 1));
        param_values.push(Box::new(explanation.clone()));
    }
    if let Some(superseded_by) = &patch.superseded_by {
        sets.push(format!("superseded_by = ?{}", param_values.len() + 1));
        param_values.push(Box::new(superseded_by.clone()));
    }

    if sets.is_empty() {
        return get_asset(conn, id);
    }

    let id_param_idx = param_values.len() + 1;
    param_values.push(Box::new(id.to_string()));

    let sql = format!(
        "UPDATE assets SET {} WHERE id = ?{}",
        sets.join(", "),
        id_param_idx
    );
    let params_refs: Vec<&dyn rusqlite::ToSql> = param_values.iter().map(|v| v.as_ref()).collect();
    conn.execute(&sql, params_refs.as_slice())?;
    get_asset(conn, id)
}

pub fn insert_relationship(
    conn: &Connection,
    rel: &AssetRelationship,
) -> Result<(), BriefcaseError> {
    conn.execute(
        "INSERT OR IGNORE INTO asset_relationships (source_id, target_id, relationship_type, created_at)
         VALUES (?1, ?2, ?3, ?4)",
        params![
            rel.source_id,
            rel.target_id,
            rel.relationship_type.to_string(),
            rel.created_at,
        ],
    )?;
    Ok(())
}

pub fn get_relationships(
    conn: &Connection,
    asset_id: &str,
) -> Result<Vec<AssetRelationship>, BriefcaseError> {
    let mut stmt = conn.prepare(
        "SELECT source_id, target_id, relationship_type, created_at
         FROM asset_relationships
         WHERE source_id = ?1 OR target_id = ?1",
    )?;
    let rows = stmt.query_map(params![asset_id], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
        ))
    })?;
    let mut results = Vec::new();
    for row in rows {
        let (source_id, target_id, rel_type_str, created_at) = row?;
        let relationship_type =
            RelationshipType::from_str(&rel_type_str).unwrap_or(RelationshipType::References);
        results.push(AssetRelationship {
            source_id,
            target_id,
            relationship_type,
            created_at,
        });
    }
    Ok(results)
}

fn row_to_asset(row: &rusqlite::Row<'_>) -> rusqlite::Result<AssetRecord> {
    let tags_str: String = row.get(13)?;
    let tags: Vec<String> =
        serde_json::from_str(&tags_str).unwrap_or_default();

    let importance_str: String = row.get(9)?;
    let audience_str: String = row.get(10)?;
    let confidentiality_str: String = row.get(11)?;
    let vetted_status_str: String = row.get(12)?;

    Ok(AssetRecord {
        id: row.get(0)?,
        content_hash: row.get(1)?,
        title: row.get(2)?,
        file_type: row.get(3)?,
        original_name: row.get(4)?,
        project: row.get(5)?,
        subproject: row.get(6)?,
        source_agent: row.get(7)?,
        pipeline_id: row.get(8)?,
        importance: Importance::from_str(&importance_str).unwrap_or_default(),
        audience: Audience::from_str(&audience_str).unwrap_or_default(),
        confidentiality: Confidentiality::from_str(&confidentiality_str).unwrap_or_default(),
        vetted_status: VettedStatus::from_str(&vetted_status_str).unwrap_or_default(),
        tags,
        classification_confidence: row.get(14)?,
        classification_explanation: row.get(15)?,
        created_at: row.get(16)?,
        ingested_at: row.get(17)?,
        version: row.get(18)?,
        superseded_by: row.get(19)?,
    })
}

// ── Phase 2: Collections schema + CRUD ───────────────────────────────────────

pub fn initialize_collections_schema(conn: &Connection) -> Result<(), crate::error::BriefcaseError> {
    conn.execute_batch(
        r#"
        CREATE TABLE IF NOT EXISTS collections (
            id             TEXT PRIMARY KEY,
            name           TEXT NOT NULL,
            description    TEXT NOT NULL DEFAULT '',
            cover_asset_id TEXT REFERENCES assets(id) ON DELETE SET NULL,
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS collection_items (
            collection_id TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
            asset_id      TEXT NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
            position      INTEGER NOT NULL DEFAULT 0,
            slide_notes   TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (collection_id, asset_id)
        );

        CREATE INDEX IF NOT EXISTS idx_ci_collection ON collection_items(collection_id, position);
        "#,
    )?;
    Ok(())
}

// ── Collection CRUD ───────────────────────────────────────────────────────────

use crate::models::collection::{Collection, CollectionItem};

pub fn insert_collection(conn: &Connection, c: &Collection) -> Result<(), crate::error::BriefcaseError> {
    conn.execute(
        "INSERT INTO collections (id, name, description, cover_asset_id, created_at, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        params![c.id, c.name, c.description, c.cover_asset_id, c.created_at, c.updated_at],
    )?;
    Ok(())
}

pub fn get_collection(conn: &Connection, id: &str) -> Result<Collection, crate::error::BriefcaseError> {
    let mut stmt = conn.prepare(
        "SELECT c.id, c.name, c.description, c.cover_asset_id, c.created_at, c.updated_at,
                COUNT(ci.asset_id) AS item_count
         FROM collections c
         LEFT JOIN collection_items ci ON ci.collection_id = c.id
         WHERE c.id = ?1
         GROUP BY c.id",
    )?;
    let result = stmt.query_row(params![id], row_to_collection).map_err(|_| {
        crate::error::BriefcaseError::NotFound { id: id.to_string() }
    })?;
    Ok(result)
}

pub fn list_collections(conn: &Connection) -> Result<Vec<Collection>, crate::error::BriefcaseError> {
    let mut stmt = conn.prepare(
        "SELECT c.id, c.name, c.description, c.cover_asset_id, c.created_at, c.updated_at,
                COUNT(ci.asset_id) AS item_count
         FROM collections c
         LEFT JOIN collection_items ci ON ci.collection_id = c.id
         GROUP BY c.id
         ORDER BY c.updated_at DESC",
    )?;
    let rows = stmt.query_map([], row_to_collection)?;
    let mut results = Vec::new();
    for row in rows {
        results.push(row?);
    }
    Ok(results)
}

pub fn update_collection(
    conn: &Connection,
    id: &str,
    name: &str,
    description: &str,
    cover_asset_id: Option<&str>,
    updated_at: &str,
) -> Result<(), crate::error::BriefcaseError> {
    conn.execute(
        "UPDATE collections SET name = ?1, description = ?2, cover_asset_id = ?3, updated_at = ?4
         WHERE id = ?5",
        params![name, description, cover_asset_id, updated_at, id],
    )?;
    Ok(())
}

pub fn delete_collection(conn: &Connection, id: &str) -> Result<(), crate::error::BriefcaseError> {
    conn.execute("DELETE FROM collections WHERE id = ?1", params![id])?;
    Ok(())
}

// ── Collection item operations ────────────────────────────────────────────────

pub fn get_collection_items(
    conn: &Connection,
    collection_id: &str,
) -> Result<Vec<CollectionItem>, crate::error::BriefcaseError> {
    let mut stmt = conn.prepare(
        "SELECT collection_id, asset_id, position, slide_notes
         FROM collection_items
         WHERE collection_id = ?1
         ORDER BY position ASC",
    )?;
    let rows = stmt.query_map(params![collection_id], |row| {
        Ok(CollectionItem {
            collection_id: row.get(0)?,
            asset_id: row.get(1)?,
            position: row.get(2)?,
            slide_notes: row.get(3)?,
        })
    })?;
    let mut results = Vec::new();
    for row in rows {
        results.push(row?);
    }
    Ok(results)
}

pub fn add_to_collection(
    conn: &Connection,
    collection_id: &str,
    asset_id: &str,
    slide_notes: &str,
) -> Result<(), crate::error::BriefcaseError> {
    // Append at the end: max(position) + 1
    let max_pos: i64 = conn.query_row(
        "SELECT COALESCE(MAX(position), -1) FROM collection_items WHERE collection_id = ?1",
        params![collection_id],
        |row| row.get(0),
    )?;
    conn.execute(
        "INSERT OR IGNORE INTO collection_items (collection_id, asset_id, position, slide_notes)
         VALUES (?1, ?2, ?3, ?4)",
        params![collection_id, asset_id, max_pos + 1, slide_notes],
    )?;
    // Touch updated_at on the parent collection
    let now = chrono::Utc::now().to_rfc3339();
    conn.execute(
        "UPDATE collections SET updated_at = ?1 WHERE id = ?2",
        params![now, collection_id],
    )?;
    Ok(())
}

pub fn remove_from_collection(
    conn: &Connection,
    collection_id: &str,
    asset_id: &str,
) -> Result<(), crate::error::BriefcaseError> {
    conn.execute(
        "DELETE FROM collection_items WHERE collection_id = ?1 AND asset_id = ?2",
        params![collection_id, asset_id],
    )?;
    Ok(())
}

pub fn reorder_collection_item(
    conn: &Connection,
    collection_id: &str,
    asset_id: &str,
    position: i64,
) -> Result<(), crate::error::BriefcaseError> {
    conn.execute(
        "UPDATE collection_items SET position = ?1 WHERE collection_id = ?2 AND asset_id = ?3",
        params![position, collection_id, asset_id],
    )?;
    Ok(())
}

/// Used by the FORGE listener to check for duplicates before ingesting.
pub fn find_by_hash(
    conn: &Connection,
    hash: &str,
) -> Result<Option<AssetRecord>, crate::error::BriefcaseError> {
    let mut stmt = conn.prepare(
        "SELECT id, content_hash, title, file_type, original_name,
                project, subproject, source_agent, pipeline_id,
                importance, audience, confidentiality, vetted_status,
                tags, classification_confidence, classification_explanation,
                created_at, ingested_at, version, superseded_by
         FROM assets WHERE content_hash = ?1 LIMIT 1",
    )?;
    match stmt.query_row(params![hash], row_to_asset) {
        Ok(record) => Ok(Some(record)),
        Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
        Err(e) => Err(crate::error::BriefcaseError::Database(e)),
    }
}

fn row_to_collection(row: &rusqlite::Row<'_>) -> rusqlite::Result<Collection> {
    Ok(Collection {
        id: row.get(0)?,
        name: row.get(1)?,
        description: row.get(2)?,
        cover_asset_id: row.get(3)?,
        created_at: row.get(4)?,
        updated_at: row.get(5)?,
        item_count: row.get(6)?,
    })
}
