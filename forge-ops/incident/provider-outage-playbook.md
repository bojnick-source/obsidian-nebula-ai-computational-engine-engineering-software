# Provider Outage Playbook

> What to do when an LLM provider is unavailable.

---

## Detection

Provider outage detected when:
- Health check fails >30s continuously
- `ERR_PROVIDER_UNAVAILABLE` logged >3 times in 60s
- `DEGRADED_PROVIDER` mode activates

---

## Response Steps

### Step 1: Confirm outage (< 2 min)
```
1. Check provider status page (Anthropic: https://status.anthropic.com)
2. Verify it's not a local network/auth issue
3. Log: degraded_mode_activated with trigger details
```

### Step 2: Activate failover (< 5 min)
- At MVP: no automatic failover (single provider). Queue tasks.
- At V1: router automatically tries secondary provider chain.

```
[V1] Failover chain: anthropic → openai → degraded_lite_mode
```

### Step 3: Communicate
- Alert engineering team via configured channel
- Update task queue status to "paused pending provider recovery"

### Step 4: Monitor recovery
- Check health every 30s
- Log `degraded_mode_deactivated` when provider recovers
- Resume queued tasks in order

### Step 5: Post-incident
- Document in incident log: duration, tasks affected, recovery time
- Update provider reliability metrics
