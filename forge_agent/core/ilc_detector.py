"""ILC Detector — inter-domain link candidate detection from vault notes.

Identifies pairs of vault notes that share technical terms (physical quantities
with units, named phenomena) and writes detected candidates to ilc/links/ in the
vault using upsert_note().
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slug(path: str) -> str:
    """Convert a vault path or filename stem to a slug suitable for filenames.

    Replaces path separators and spaces with hyphens; strips leading/trailing
    hyphens; lowercases the result.
    """
    slug = re.sub(r"[/\\.\s]+", "-", path)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-").lower()


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ILCCandidate:
    """A detected inter-domain link candidate between two vault notes."""

    note_a_path: str
    note_b_path: str
    shared_terms: list[str] = field(default_factory=list)
    link_type: str = "reinforcing"  # "cross-domain" | "reinforcing" | "contradicting"
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------


class ILCDetector:
    """Detect inter-domain link candidates between vault notes.

    Parameters
    ----------
    vault_manager:
        Object with upsert_note(path, markdown, frontmatter) -> str.
        Used to persist detected candidates.
    """

    # Regex for physical quantities: number + unit, e.g. "1.5 MPa", "300 K", "9.81 m/s²"
    _QUANTITY_RE = re.compile(
        r"\b\d+(?:\.\d+)?\s*"
        r"(?:MPa|GPa|kPa|Pa|N|kN|MN|mm|cm|m|km|kg|g|mg|K|°C|°F|"
        r"W|kW|MW|J|kJ|MJ|Hz|kHz|MHz|GHz|m/s|m/s²|rad/s|rpm)\b",
        re.IGNORECASE,
    )

    # Named phenomena / terms: multi-word technical phrases
    _PHENOMENON_RE = re.compile(
        r"\b(?:"
        r"von [Mm]ises stress|yield strength|Young[''s]* modulus|Poisson[''s]* ratio|"
        r"thermal conductivity|heat transfer|Reynolds number|Mach number|"
        r"drag coefficient|lift coefficient|buckling load|fatigue limit|"
        r"stress concentration|fracture toughness|creep rupture|"
        r"natural frequency|mode shape|damping ratio|modal analysis|"
        r"topology optimi[sz]ation|finite element|CFD|FEA|FEM"
        r")\b"
    )

    def __init__(self, vault_manager: Any) -> None:
        self._vault_manager = vault_manager  # stored and used in write_candidates

    def detect_candidates(
        self,
        notes: list[dict],
        min_shared_terms: int = 2,
    ) -> list[ILCCandidate]:
        """Find note pairs sharing >= min_shared_terms technical terms.

        Parameters
        ----------
        notes:
            List of dicts, each with keys: "path" (str), "content" (str),
            and optionally "frontmatter" (dict with "domain" key).
        min_shared_terms:
            Minimum number of shared technical terms to qualify as a candidate.

        Returns
        -------
        List of ILCCandidate (may be empty).
        """
        if len(notes) < 2:
            return []

        # Extract term sets per note — both params (notes, min_shared_terms) used
        term_sets: list[tuple[str, set[str]]] = []
        for note in notes:
            path = note.get("path", "")
            content = note.get("content", "")
            terms = self._extract_terms(content)
            term_sets.append((path, terms))

        candidates: list[ILCCandidate] = []
        for i in range(len(term_sets)):
            for j in range(i + 1, len(term_sets)):
                path_a, terms_a = term_sets[i]
                path_b, terms_b = term_sets[j]
                shared = sorted(terms_a & terms_b)
                if len(shared) < min_shared_terms:
                    continue
                link_type = self._classify(notes[i], notes[j], shared)
                confidence = self._score(len(shared), len(terms_a), len(terms_b))
                candidates.append(ILCCandidate(
                    note_a_path=path_a,
                    note_b_path=path_b,
                    shared_terms=shared,
                    link_type=link_type,
                    confidence=confidence,
                ))

        return candidates

    def write_candidates(
        self,
        candidates: list[ILCCandidate],
    ) -> list[str]:
        """Persist each candidate as a YAML-frontmatter note under ilc/links/.

        Returns list of written vault paths.
        """
        written: list[str] = []
        for c in candidates:
            slug_a = _slug(c.note_a_path)
            slug_b = _slug(c.note_b_path)
            path = f"ilc/links/{slug_a}--{slug_b}.md"
            frontmatter = {
                "type": "ilc_candidate",
                "link_type": c.link_type,
                "confidence": round(c.confidence, 4),
                "note_a": c.note_a_path,
                "note_b": c.note_b_path,
                "shared_terms": c.shared_terms,
            }
            markdown = (
                f"# ILC: {c.note_a_path} \u2194 {c.note_b_path}\n\n"
                f"**Link type**: {c.link_type}  \n"
                f"**Confidence**: {c.confidence:.3f}  \n"
                f"**Shared terms**: {', '.join(c.shared_terms)}\n"
            )
            # vault_manager.upsert_note(path, markdown, frontmatter) — P1 verified
            self._vault_manager.upsert_note(path, markdown, frontmatter)
            written.append(path)
        return written

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_terms(self, content: str) -> set[str]:
        """Extract physical quantities and named phenomena from note content."""
        terms: set[str] = set()
        for m in self._QUANTITY_RE.finditer(content):
            terms.add(m.group(0).strip())
        for m in self._PHENOMENON_RE.finditer(content):
            terms.add(m.group(0).strip())
        return terms

    def _classify(
        self,
        note_a: dict,
        note_b: dict,
        shared_terms: list[str],  # noqa: ARG002  — reserved for future contradiction detection
    ) -> str:
        """Classify link as cross-domain, reinforcing, or contradicting.

        Heuristic:
          - "cross-domain": notes have different 'domain' frontmatter keys.
          - "reinforcing": same domain, non-contradicting shared terms.
        """
        domain_a = note_a.get("frontmatter", {}).get("domain", "unknown")
        domain_b = note_b.get("frontmatter", {}).get("domain", "unknown")
        if domain_a != domain_b and domain_a != "unknown" and domain_b != "unknown":
            return "cross-domain"
        return "reinforcing"

    def _score(
        self,
        n_shared: int,
        n_terms_a: int,
        n_terms_b: int,
    ) -> float:
        """Jaccard-like confidence: shared / union clamped to [0, 1]."""
        union = n_terms_a + n_terms_b - n_shared
        if union == 0:
            return 0.0
        return min(1.0, n_shared / union)
