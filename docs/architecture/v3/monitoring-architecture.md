# Monitoring Architecture (Context 1D)

> Incremental four-layer monitoring stack. No web infrastructure on day one.
> Solo developer "glance dashboard": 4 numbers + 7-day cost trend + agent performance bars.

---

## Four Layers (incremental)

| Layer | Timeline | Tools | Cost |
|---|---|---|---|
| L1 | Day 1 | structlog + DuckDB | Free |
| L2 | Week 1 | Uptime Kuma | Free (self-hosted) |
| L3 | Week 2 | Coolify | Free (self-hosted) |
| L4 | Month 2 | Grafana + OpenLIT + Loki | ~$20/month VPS |

---

## Layer 1: Structured Logging + DuckDB (Day 1)

### structlog configuration

```python
# forge-output/src/forge_output/logging_config.py
import structlog
import logging
from datetime import datetime

def configure_logging(log_dir: str = "logs") -> None:
    Path(log_dir).mkdir(exist_ok=True)
    log_file = Path(log_dir) / f"forge-{datetime.today().strftime('%Y-%m-%d')}.jsonl"

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.WriteLoggerFactory(
            file=log_file.open("a")
        ),
    )
```

### DuckDB queries (no server, no import)

```sql
-- Daily cost by provider
SELECT provider, model,
       SUM(cost_usd) as total_cost_usd,
       COUNT(*) as call_count,
       SUM(tokens_in + tokens_out) as total_tokens
FROM read_json_auto('logs/*.jsonl')
WHERE ts > '2026-03-01'
  AND event = 'phase_end'
GROUP BY provider, model
ORDER BY total_cost_usd DESC;

-- Agent success rates (last 7 days)
SELECT agent, COUNT(*) as total_runs,
       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successes,
       ROUND(100.0 * SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) / COUNT(*), 1) as success_rate_pct
FROM read_json_auto('logs/*.jsonl')
WHERE ts > NOW() - INTERVAL '7 days'
  AND event = 'phase_end'
GROUP BY agent
ORDER BY success_rate_pct;

-- Error frequency by error_code
SELECT error_code, COUNT(*) as occurrences
FROM read_json_auto('logs/*.jsonl')
WHERE event = 'error' AND ts > NOW() - INTERVAL '24 hours'
GROUP BY error_code
ORDER BY occurrences DESC;
```

---

## Layer 2: Uptime Kuma (Week 1)

```bash
docker run -d --restart=always -p 3001:3001 \
  -v uptime-kuma:/app/data \
  louislam/uptime-kuma:1
```

Monitors:
- Anthropic API health: `https://status.anthropic.com/api/v2/status.json`
- OpenAI API health: `https://status.openai.com/api/v2/status.json`
- Supermemory service: `https://api.supermemory.ai/health`
- Local Langfuse: `http://localhost:3000/health`

Notifications: Discord webhook (free) or Telegram bot.

---

## Layer 3: Coolify (Week 2)

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

Manages all FORGE services from a single UI:
- Deploy from Git on push
- Manage Docker containers (Langfuse, Uptime Kuma, etc.)
- Automatic SSL certificates
- Environment variable management (no `.env` files in git)
- Deployment failure notifications

---

## Layer 4: Grafana + OpenLIT (Month 2)

### OpenLIT auto-instrumentation

```python
import openlit
openlit.init(
    otlp_endpoint="http://localhost:4317",
    application_name="forge"
)
# All Anthropic/OpenAI calls now traced to Prometheus + Langfuse
```

### Key Grafana dashboards

**"Glance" dashboard — 4 number tiles + trends:**
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Today's Cost │ Active Agents│ Completed 24h│ Error Count  │
│   $0.34      │      3       │     12       │      1       │
└──────────────┴──────────────┴──────────────┴──────────────┘

7-Day Cost by Provider (stacked area chart)
█████████████████████████████████
anthropic ████████████████████ $2.10
openai    ██████              $0.80

Agent Performance (horizontal bar, color-coded by level)
me_specialist     [L3] ████████████████████ 94%
librarian         [L2] ████████████████     89%
struct_verifier   [L2] ████████████████████ 100%
```

### Prometheus metrics (from OpenLIT)

```
# HELP forge_api_cost_usd_total Total API cost by provider
forge_api_cost_usd_total{provider="anthropic",model="claude-opus-4-6"} 2.34

# HELP forge_agent_duration_seconds Agent execution time
forge_agent_duration_seconds_bucket{agent="me_specialist",le="1.0"} 5
forge_agent_duration_seconds_bucket{agent="me_specialist",le="5.0"} 18

# HELP forge_verification_gate_total Verification gate results
forge_verification_gate_total{gate="contract",result="pass"} 47
forge_verification_gate_total{gate="unit",result="fail"} 3

# HELP forge_vault_amnesia_check_total Vault amnesia check results
forge_vault_amnesia_check_total{result="pass"} 52
forge_vault_amnesia_check_total{result="fail"} 0
```

### Loki + LogQL for structured JSONL queries

```logql
# All error events with their error_codes (last hour)
{job="forge"} | json | event="error" | line_format "{{.ts}} {{.error_code}} {{.agent}}"

# Verification gate failures
{job="forge"} | json | event="verification_gate" AND result="fail"
  | line_format "{{.ts}} gate={{.meta.gate}} agent={{.agent}} code={{.error_code}}"
```

---

## Cost Tracking Event Schema

Every LLM API call emits a cost event (from OpenLIT, supplemented by FORGE):

```json
{
  "ts": "ISO8601",
  "event": "api_cost",
  "run_id": "forge-042",
  "trace_id": "uuid-v4",
  "agent": "me_specialist",
  "provider": "anthropic",
  "model": "claude-opus-4-6",
  "tokens_in": 4200,
  "tokens_out": 680,
  "cost_usd": 0.0312,
  "phase": "specialist"
}
```

Budget thresholds (configured in `forge-ops/cost/budget-thresholds.md`):
- Per-run alert: >$1.00
- Daily alert: >$10.00
- Monthly alert: >$100.00

---

## Total Infrastructure Cost Estimate

| Component | Cost/month |
|---|---|
| Anthropic API (typical usage) | $30–60 |
| Supermemory | $10–20 |
| VPS for Grafana + Loki + Langfuse | $10–20 |
| Uptime Kuma + Coolify | Free (self-hosted) |
| Semantic Scholar + arXiv + OpenAlex | Free |
| **Total** | **~$50–100/month** |
