# HashiCorp Vault Secret Paths

> V1 feature. MVP uses environment variables. HCV required before V1 ships.

---

## Secret Path Structure

```
forge/
  providers/
    anthropic/
      api_key          # Anthropic API key
    openai/
      api_key          # OpenAI API key (V1 failover)
  infrastructure/
    vault_backup/
      s3_access_key    # Backup storage credentials
      s3_secret_key
  signing/
    forge_signing_key  # Code signing key (future)
```

---

## AppRole Configuration

FORGE uses HashiCorp Vault AppRole authentication.

- Role: `forge-runtime`
- Policies: `forge-provider-read`, `forge-backup-write`
- Token TTL: 1h (rotated automatically by forge-runtime on startup)

---

## Secret Rotation Policy

See `secret-rotation-policy.md`.

Short form:
- API keys: rotate every 90 days (or immediately on suspected compromise)
- Infrastructure keys: rotate every 30 days
- Rotation logged with timestamp in HCV audit log

---

## Pre-commit Secret Scanning

See `precommit-secrets-scan.md`.

All git commits are scanned for secrets before push. Uses `detect-secrets`.
CI also runs `detect-secrets scan` on every PR.
