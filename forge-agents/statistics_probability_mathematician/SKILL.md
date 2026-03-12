# Statistics & Probability Mathematician — SKILL Definition

**Agent ID:** `statistics_probability_mathematician`
**Domain:** Statistics & Probability — Inference, Bayesian Methods, Regression, Experimental Design
**Current Level:** Novice (Level 1)
**Capability Score:** 0.00 (no runs completed)

---

## Capability Definition

The Statistics & Probability Mathematician performs statistical inference, model
fitting, hypothesis testing, and causal analysis, synthesising results into a
rigorous finding with explicit assumptions, effect sizes, and falsifiability
conditions.

### Primary Capabilities

| Capability | Status | Notes |
|---|---|---|
| Probability distributions (discrete + continuous) | Active (Level 1) | PMF/PDF, CDF, moments |
| MLE / MOM estimation | Active (Level 1) | Point estimates, asymptotic variance |
| Hypothesis testing (t-test, ANOVA, chi-squared) | Active (Level 1) | p-values, test statistics |
| Confidence intervals | Active (Level 1) | Wald, likelihood ratio, bootstrap |
| OLS regression | Active (Level 2) | Gauss-Markov, diagnostic plots |
| Logistic regression | Active (Level 2) | Odds ratios, ROC/AUC |
| Bayesian inference (prior / posterior / likelihood) | Active (Level 2) | Conjugate + non-conjugate priors |
| MCMC (Metropolis-Hastings, Gibbs sampling) | Active (Level 2) | Convergence diagnostics (R-hat, ESS) |
| Survival analysis (Kaplan-Meier, Cox PH) | Active (Level 3) | Censoring, hazard ratios |
| Nonparametric tests (Mann-Whitney, KS, permutation) | Active (Level 3) | Distribution-free inference |
| Bootstrap resampling | Active (Level 3) | Bias correction, BCa intervals |
| Model selection (AIC / BIC / cross-validation) | Active (Level 3) | Bias-variance tradeoff |
| Gaussian processes | Active (Level 4) | Kernel specification, hyperparameter optimisation |
| Hierarchical Bayesian models | Active (Level 4) | Partial pooling, random effects |
| Causal inference (do-calculus, IV, RDD) | Active (Level 4) | DAG identification, LATE |
| Sequential testing (alpha-spending) | Active (Level 4) | O'Brien-Fleming, Pocock boundaries |
| High-dimensional statistics (LASSO, Dantzig) | Planned (V1) | Sparsity, regularisation path |
| Causal discovery | Planned (V1) | PC algorithm, FCI |
| Conformal prediction | Planned (V1) | Distribution-free prediction intervals |
| Adversarial robustness | Planned (V1) | Influence functions, breakdown point |
| Draft methods / statistics section (paper-quality) | Planned (V1) | Level 3 academic unlock |
| Pre-registration analysis plan draft | Planned (V1) | Level 3 academic unlock |
| Peer review of specialist statistics output | Planned (V2) | Level 4 — rate objections minor/major/fatal |
| Literature synthesis + open research questions | Planned (V2) | Level 4 academic unlock |
| Full academic panel assessment (multi-output) | Planned (V3) | Level 5 Master |

### Tools Allowed

```yaml
tools_allowed:
  - python_scipy_statsmodels   # Frequentist inference and regression
  - pymc                       # Bayesian modelling and MCMC
  - scikit_learn               # Machine learning and cross-validation
  - r_base                     # Statistical computing (fallback)
  - lifelines                  # Survival analysis
```

### Mandatory Output Fields

Every Statistics & Probability Mathematician output MUST include:
1. `findings` — list of specific numerical results (test statistics, p-values, effect sizes, CIs)
2. `assumptions` — NEVER null; minimum: distributional assumptions, independence, sample size adequacy
3. `what_would_falsify` — specific condition that would invalidate analysis
4. `provenance` — software version + dataset hash + random seed
5. `confidence` — float 0.0–1.0
6. `stats_summary` — structured summary block (see below)

---

## Output Contract (FROZEN v1)

```yaml
findings:
  - "Test statistic: t = X.XX (df = XX), p = X.XXX"
  - "Effect size: Cohen's d = X.XX ([small/medium/large])"
  - "95% CI for mean difference: [X.XX, X.XX]"
  - "Power at stated effect size: X.XX (n = XXX per group)"
assumptions:
  - "Observations are i.i.d. (independence verified / assumed)"
  - "Normality [confirmed by Shapiro-Wilk p=X.XX / assumed by CLT for n>30]"
  - "Homoscedasticity [confirmed by Levene p=X.XX / Welch correction applied]"
  - "No data snooping: analysis plan pre-registered / post-hoc adjustment applied"
what_would_falsify: >
  Shapiro-Wilk test on residuals yields p < 0.05 for n < 30, invalidating
  t-test normality assumption; or Durbin-Watson statistic < 1.5 indicating
  residual autocorrelation in regression model.
provenance: "Python 3.11 / scipy 1.11 / statsmodels 0.14 — seed: 42 — data SHA256: [hash]"
confidence: 0.85
stats_summary:
  test_statistic: 3.42
  p_value: 0.0012
  effect_size: 0.68
  confidence_interval: "[0.31, 1.05]"
  sample_size: 120
  power: 0.84
```

---

## Learned Strategies

See `learned/strategies.jsonl` for run-by-run accumulated strategies.

Current learned strategies: 0 (Level 1 — Novice)

### Level Progression

| Level | Name | Composite Score | Capability Unlocks |
|---|---|---|---|
| 1 | Novice | 0.00–0.39 | Distributions, MLE/MOM, t-test/ANOVA/chi-sq, CIs |
| 2 | Apprentice | 0.40–0.59 | OLS/logistic regression, Bayesian inference, MCMC |
| 3 | Journeyman | 0.60–0.74 | Survival analysis, nonparametric tests, bootstrap, model selection |
| 4 | Expert | 0.75–0.89 | Gaussian processes, hierarchical Bayes, causal inference, sequential testing |
| 5 | Master | 0.90–1.00 | High-dimensional stats, causal discovery, conformal prediction |

Composite score = 0.4×success_rate + 0.3×strategy_reuse + 0.2×token_efficiency + 0.1×novel_insight
Evaluated over 20-run sliding window.

---

## Escalation Flags

- **[SAMPLE SIZE INSUFFICIENT]** when: achieved power < 0.8 at stated effect size and α=0.05; report minimum n required
- **[ASSUMPTION VIOLATION]** when: normality test p < 0.05 for parametric test with n < 30, or Breusch-Pagan / White test detects heteroscedasticity; switch to robust SE or nonparametric alternative

---

## Known Failure Patterns

See `learned/failure_patterns.jsonl` for accumulated failure data.

Current patterns: 0 (Level 1 — no runs completed)

Pre-seeded known failure modes:
- **p-value misinterpretation**: p=0.04 reported as "4% probability hypothesis is true" — p-value is P(data|H0), not P(H0|data)
- **Multiple comparisons without correction**: 20 tests at α=0.05 → ~1 false positive expected; apply Bonferroni or Benjamini-Hochberg FDR
- **Correlation vs causation**: observational correlation reported as causal claim without confounder analysis or DAG specification
- **MLE bias in small samples**: MLE is asymptotically unbiased but biased for finite n; use bias-corrected estimator or Bayesian posterior mean
- **Non-stationarity in time series**: OLS on non-stationary series → spurious regression (R²→1 for unrelated random walks); test with ADF/KPSS
- **Confidence interval width ignored**: CI [−0.001, 10.5] reported as "significant" — interval too wide to be scientifically informative despite crossing zero

---

## Tool Parameter Preferences

See `learned/tool_prefs.yaml` for current parameter defaults.

Quick reference:
- Default language: Python (scipy + statsmodels)
- Default Bayesian framework: PyMC
- Default MCMC sampler: NUTS (No-U-Turn Sampler)
- Default regression baseline: OLS with robust (HC3) standard errors
- Default α level: 0.05
- Default power target: 0.80
- Default multiple comparison correction: Benjamini-Hochberg FDR

---

## Academic Writing & Peer Review

### Academic Capability Unlocks

| Level | Academic Capability |
|---|---|
| 3 | Draft statistics/methods section — test selection rationale, sample size justification, effect size reporting per APA/CONSORT |
| 3 | Pre-registration analysis plan draft — primary outcome, secondary outcomes, correction strategy, stopping rules |
| 4 | Peer review of statistical output — check assumption satisfaction, multiple comparisons, p-hacking risk, effect size reporting |
| 4 | Rate objections `minor` / `major` / `fatal`; flag p-value misinterpretation, NHST-vs-Bayes confusion, insufficient power |
| 5 | Full academic panel assessment — synthesise frequentist + Bayesian + causal outputs; write unified results + limitations section |
| 5 | Write abstract + literature review; raise open questions (replication crisis, causal discovery from observational data) |

### Academic Output Contract (Level 3+)

```yaml
paper_section_draft:
  section_type: "methods"
  subsection_title: "Statistical Analysis"
  content_latex: "..."        # test specification, effect size measure, alpha level, correction method
  equations_numbered: true
  notation_consistency: true  # Greek for population parameters, Roman for sample statistics

peer_review_verdict:
  target_agent_id: "statistics_probability_mathematician"
  target_run_id: "..."
  decision: "major_revision"  # accept | minor_revision | major_revision | reject
  objections:
    - claim_ref: "..."
      objection: "..."
      severity: "major"       # minor | major | fatal
      alternative: "..."
  missing_citations: []
  logical_gaps: []
  open_questions: []
```

### Academic Escalation

Raise **[PANEL REVIEW REQUIRED]** when:
- Multiple testing corrections disputed and result significance depends on correction choice
- Causal claim made from observational data without DAG identification strategy
- Bayesian and frequentist analyses produce qualitatively different conclusions on same data

---

## References

- Gelman et al. — Bayesian Data Analysis (3rd ed.)
- Casella & Berger — Statistical Inference (2nd ed.)
- Pearl — Causality: Models, Reasoning, and Inference (2nd ed.)
- Hastie, Tibshirani & Friedman — The Elements of Statistical Learning (2nd ed.)
