"""
forge_agent/memory/obsidian_mcp_server.py

FIX APPLIED: MCP decorator consistency.
Previously mixed bare mcp.server.Server syntax with FastMCP @app.tool() decorators.
Now uses FastMCP throughout — one pattern, no mixed imports.

Run:  python obsidian_mcp_server.py /path/to/vault
"""

import logging
import sys
from pathlib import Path

# ── FIX: Single import path — FastMCP only ───────────────────────────────────
#
# Previously: mixed the bare mcp.server.Server class with @app.tool() decorators
# which is FastMCP syntax — two incompatible patterns in one file.
# Chose FastMCP because:
#   - @app.tool() decorator is cleaner
#   - Auto-handles schema generation from type hints
#   - stdio_server transport built in via app.run()
#   - No manual request routing boilerplate

from mcp.server.fastmcp import FastMCP

# Internal vault manager (filesystem-direct, no Obsidian app dependency)
from forge_agent.memory.obsidian_manager import ObsidianVaultManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Server init ──────────────────────────────────────────────────────────────


def create_server(vault_path: str) -> FastMCP:
    """
    Create and configure the Obsidian MCP server.

    Returns a FastMCP instance with all six tools registered.
    Kept as a factory function so tests can inject mock vault_path.
    """
    app = FastMCP(
        name="obsidian-vault",
        instructions=(
            "Access the FORGE engineering knowledge vault. "
            "Use search_notes first to find relevant content. "
            "Use get_note when you know the exact path. "
            "Only Librarian and Verifier roles may call upsert_note."
        ),
    )

    vault = ObsidianVaultManager(vault_path)
    logger.info("Vault loaded: %s (%d notes indexed)", vault_path, len(vault._index))

    # ── READ TOOLS ────────────────────────────────────────────────────────────

    @app.tool()
    def search_notes(
        query: str,
        top_k: int = 5,
        domain: str | None = None,
        tags: list[str] | None = None,
        min_confidence: float | None = None,
    ) -> list[dict]:
        """
        Search vault notes by keyword (or semantic if embedding model configured).

        Args:
            query:          Natural language search query
            top_k:          Maximum number of results (default 5)
            domain:         Optional subdirectory filter, e.g. "engineering/constraints"
            tags:           Optional tag filter, e.g. ["validated", "derivation"]
            min_confidence: Optional minimum frontmatter confidence score (0.0-1.0)

        Returns:
            List of {path, title, excerpt, frontmatter, score, backlinks}
        """
        results = vault.search_notes(
            query=query,
            top_k=top_k,
            domain=domain,
            tags=tags,
            min_confidence=min_confidence,
        )
        # Serialize dataclasses to plain dicts for MCP transport
        return [
            {
                "path":        r.path,
                "title":       r.title,
                "excerpt":     r.excerpt,
                "frontmatter": r.frontmatter,
                "score":       r.score,
                "backlinks":   r.backlinks,
            }
            for r in results
        ]

    @app.tool()
    def get_note(path: str) -> dict | None:
        """
        Retrieve a specific note by its vault-relative path.

        Args:
            path: Vault-relative path, e.g. "engineering/constraints/max_thrust.md"

        Returns:
            {path, title, frontmatter, body, sections, tags, outgoing_links, modified}
            or None if not found.
        """
        note = vault.get_note(path)
        if note is None:
            return None
        return {
            "path":           note.path,
            "title":          note.title,
            "frontmatter":    note.frontmatter,
            "body":           note.body,
            "sections":       note.sections,
            "tags":           note.tags,
            "outgoing_links": note.outgoing_links,
            "modified":       note.modified,
        }

    @app.tool()
    def get_backlinks(path: str) -> list[str]:
        """
        Return all note paths that link TO this note via [[wiki links]].

        Useful for tracing dependency chains:
        "What derivations depend on this constraint?"
        """
        return vault.get_backlinks(path)

    @app.tool()
    def get_tags(tag: str) -> list[str]:
        """
        Return all note paths that carry a given tag.

        Convention tags:
          validated, draft, stale, constraint, derivation, decision,
          failure-mode, pattern
        """
        return vault.get_tags(tag)

    # ── WRITE TOOLS ───────────────────────────────────────────────────────────

    @app.tool()
    def upsert_note(
        path: str,
        markdown: str,
        frontmatter: dict | None = None,
        provenance: dict | None = None,
    ) -> str:
        """
        Create or overwrite a vault note.

        SECURITY: Only Librarian and Verifier agents should call this.
        Governance layer enforces write permissions before reaching here.

        Args:
            path:        Vault-relative path (will be created if missing)
            markdown:    Full markdown body (no frontmatter — pass separately)
            frontmatter: Dict merged on top of existing frontmatter
            provenance:  {model, agent, session_id, iteration} for audit trail

        Returns:
            Absolute path of the written file.
        """
        return vault.upsert_note(
            path=path,
            markdown=markdown,
            frontmatter=frontmatter,
            provenance=provenance,
        )

    @app.tool()
    def append_to_note(path: str, markdown: str) -> str:
        """
        Append markdown content to an existing note.

        Creates the note if it doesn't exist.
        Used for: simulation logs, failure catalogs, check results.

        Returns:
            Absolute path of the modified file.
        """
        return vault.append_to_note(path=path, markdown=markdown)

    @app.tool()
    def add_frontmatter(path: str, yaml_patch: dict) -> str:
        """
        Patch frontmatter fields without touching the note body.

        Used for:
          - Stamping confidence: 0.95 after Verifier approval
          - Changing status: draft → validated
          - Adding tags: [validated, production-ready]
          - Flagging disputes: status: disputed

        Returns:
            Absolute path of the modified file.
        """
        return vault.add_frontmatter(path=path, yaml_patch=yaml_patch)

    return app


# ── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python obsidian_mcp_server.py /path/to/vault", file=sys.stderr)
        sys.exit(1)

    vault_path = sys.argv[1]

    if not Path(vault_path).is_dir():
        print(f"Error: vault path does not exist: {vault_path}", file=sys.stderr)
        sys.exit(1)

    app = create_server(vault_path)

    # FastMCP handles stdio transport internally — no manual Server.run() needed.
    # This replaces the old `async with stdio_server() as (read, write): await app.run(...)`
    # which was the bare mcp.server.Server pattern.
    app.run()


if __name__ == "__main__":
    main()
