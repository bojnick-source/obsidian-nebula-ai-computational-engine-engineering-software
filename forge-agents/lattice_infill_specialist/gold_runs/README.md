# Gold Runs — Lattice Infill Specialist

This directory contains exemplary interaction records for `lattice_infill_specialist`.
Gold runs serve as positive training examples and quality benchmarks.

## File Format

Each gold run is a markdown file with YAML frontmatter:

```
---
run_id: gr-NNN
task: <one-line task description>
difficulty: easy | medium | hard | expert
outcome: pass | partial | escalation
confidence: 0.00–1.00
date: YYYY-MM-DD
tags: []
---

## Task
Full task description provided to the agent.

## Reasoning
The agent's step-by-step reasoning process.

## Answer
Final answer with units, equations, citations, and provenance.

## What Made This Good
Specific criteria: rigour, correctness, escalation behaviour, etc.
```

## Usage

Gold runs are used by:
- The learning loop to calibrate strategy selection
- The Antagonist to calibrate its false-positive rate
- Human reviewers assessing agent capability level
- Regression tests (`tests/test_gold_runs.py`)

## Status

Gold runs to be added as the agent accumulates verified correct analyses.
