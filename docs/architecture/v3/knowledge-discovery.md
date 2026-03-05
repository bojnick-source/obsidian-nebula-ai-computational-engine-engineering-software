# External Knowledge Discovery (2B)

> Scheduled cadence: daily preprint monitoring, weekly deep literature review.
> Target cost: ~$0/month for academic APIs, ~$10-20/month for web search APIs.

---

## Knowledge Source Tiers

### Tier 1: Free Academic APIs (Zero Cost)

| API | Coverage | Rate Limit | Best For |
|---|---|---|---|
| **Semantic Scholar** | 225M+ papers, SPECTER2 embeddings | 1 req/s (free key) | Primary: abstracts, citations, embeddings |
| **arXiv** | Preprints (no auth) | RSS feeds | Preprint monitoring: `cs.CE`, `physics.flu-dyn`, `math.OC` |
| **OpenAlex** | 474M+ works (CC0) | 100K req/day | Broadest coverage: books, datasets |

### Tier 2: Engineering Data APIs (Free + API key)

| API | Coverage | Notes |
|---|---|---|
| **Materials Project** | `mp-api` Python SDK | DFT-computed material properties |
| **OPTIMADE** | 10M+ entries (AFLOW, Materials Project, NOMAD) | Unified query interface |
| **NIST JANAF** | Thermochemical tables | Free web API |

### Tier 3: Web Search APIs (~$10-20/month)

| API | Cost | Best For |
|---|---|---|
| **Tavily** | ~$0.008/credit | RAG-optimized; 93.3% SimpleQA; JSON output |
| **Exa** | Variable | Neural semantic search for papers by meaning |
| **Perplexity Sonar** | $5/1K requests | Fact verification; <400ms latency |

---

## Discovery Pipeline

```python
# forge-learning/src/forge_learning/knowledge_discovery.py

class KnowledgeDiscoveryAgent:
    """
    Scheduled knowledge discovery: daily for arXiv, weekly for deep search.
    Feeds discovered knowledge through quality gate before vault storage.
    """

    def __init__(self, semantic_scholar_api_key: str,
                 tavily_api_key: str,
                 vault_writer: VaultWriter,
                 quality_evaluator: QualityEvaluator):
        self.ss = SemanticScholarAPI(api_key=semantic_scholar_api_key)
        self.tavily = TavilyClient(api_key=tavily_api_key)
        self.vault_writer = vault_writer
        self.evaluator = quality_evaluator

    def daily_arxiv_scan(self, categories: list[str] = None) -> list[KnowledgeUnit]:
        """Monitor arXiv RSS feeds for new relevant papers."""
        categories = categories or ["cs.CE", "physics.flu-dyn", "math.OC",
                                    "cond-mat.mtrl-sci"]
        papers = []
        for cat in categories:
            rss = arxiv.RSS(category=cat)  # no auth needed
            for paper in rss.entries:
                relevance = self._score_relevance(paper)
                if relevance >= 0.3:
                    papers.append(self._extract_knowledge_unit(paper))
        return papers

    def weekly_deep_review(self, queries: list[str]) -> list[KnowledgeUnit]:
        """Deep literature review using Semantic Scholar recommendation engine."""
        results = []
        for q in queries:
            papers = self.ss.search(query=q, limit=20,
                                    fields=["title", "abstract", "citations",
                                            "openAccessPdf", "embedding"])
            for paper in papers:
                if paper.influentialCitationCount > 5 or self._is_recent(paper):
                    ku = self._extract_knowledge_unit(paper)
                    results.append(ku)
        return results

    def _score_relevance(self, paper) -> float:
        """Cosine similarity between paper embedding and vault contents."""
        paper_embedding = paper.embedding.specter_v2  # SPECTER2, 768-dim
        vault_centroid = self._get_vault_centroid_embedding()
        return cosine_similarity(paper_embedding, vault_centroid)
```

---

## Scrapling: Engineering Database Scraping

```python
# For material databases and solver documentation
from scrapling import StealthyFetcher, DynamicFetcher

# Static HTML: CalculiX/OpenFOAM wikis
page = StealthyFetcher().fetch("https://www.calculix.de/CalculiX_doc.html")
content = page.find("div.doc-content").text

# JS-rendered: MatWeb material properties
fetcher = DynamicFetcher()
page = fetcher.fetch(f"https://www.matweb.com/search/datasheet.aspx?MatGUID={guid}")
props = page.find_all("td.prop-value")
```

**Target databases:**
- CalculiX documentation wiki
- OpenFOAM documentation
- MatWeb material properties (JS-rendered, needs DynamicFetcher)
- CFD-Online forums (rate-limited — 1 req/10s)

---

## Video Intelligence Pipeline

```python
# YouTube engineering lecture processing
class VideoKnowledgeExtractor:

    def extract(self, youtube_url: str) -> list[KnowledgeUnit]:
        # 1. Get timestamped transcript (no API key needed)
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # 2. For higher fidelity: download + whisper transcription
        # from faster_whisper import WhisperModel
        # model = WhisperModel("large-v3", device="cuda")
        # segments, _ = model.transcribe(audio_path)

        # 3. Segment into topic chunks
        chunks = self._segment_by_topic(transcript)

        # 4. Extract equations via Pix2Tex if slides detected
        equations = []
        for chunk in chunks:
            if chunk.has_slide:
                eq = pix2tex.recognize(chunk.slide_image)
                equations.append(eq)

        # 5. Generate knowledge units
        return [self._to_knowledge_unit(chunk, equations)
                for chunk in chunks]
```

**Recommended channels for engineering lecture knowledge:**
- MIT OpenCourseWare: structures, fluid mechanics, thermodynamics
- NPTEL: finite element analysis, CFD
- Steve Brunton (UW): data-driven engineering methods

---

## Knowledge Unit Schema

```python
@dataclass
class KnowledgeUnit:
    source_doi: str | None          # arXiv ID, DOI, or URL
    source_type: str                # "paper" | "video" | "database" | "web"
    domain: str                     # engineering domain
    key_findings: list[str]         # extracted claims
    equations: list[str]            # LaTeX strings
    applicable_conditions: list[str] # when this knowledge applies
    limitations: list[str]          # stated limitations
    extraction_confidence: float     # 0.0–1.0

    # Set by quality evaluator
    quality_score: float | None = None
    should_commit: bool = False
```

---

## Contradiction Detection

Before committing any discovered knowledge to the vault:

```python
def check_contradictions(new_ku: KnowledgeUnit,
                          existing_vault: VaultSearchIndex) -> list[Contradiction]:
    """
    High embedding similarity + divergent numerical claims → contradiction flag.
    """
    similar_notes = existing_vault.search(new_ku.content_summary, limit=10)
    contradictions = []
    for note in similar_notes:
        sim = cosine_similarity(new_ku.embedding, note.embedding)
        if sim > 0.85:  # high similarity
            numerical_conflict = _check_numerical_divergence(new_ku, note)
            if numerical_conflict:
                contradictions.append(Contradiction(
                    new_ku=new_ku,
                    existing_note=note,
                    similarity=sim,
                    conflict_type=numerical_conflict.type,
                    magnitude=numerical_conflict.magnitude
                ))
    return contradictions
```
