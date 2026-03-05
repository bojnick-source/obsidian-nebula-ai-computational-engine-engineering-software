# Vault Backup Policy

---

## Backup Method

Primary: Git-backed. Every vault write is a git commit. Full history available via `git log`.

Secondary: Snapshot archives (tar.gz) stored in `forge-vault/backups/snapshots/`.

---

## Schedule

| Backup Type | Frequency | Retention |
|---|---|---|
| Git commit (automatic) | Every write | Indefinite (git history) |
| Snapshot archive | Daily | 30 days rolling |
| Monthly archive | Monthly | 12 months |

---

## Integrity Check

After each snapshot:
1. Verify tar archive is valid (no corruption)
2. Spot-check 5 random notes for frontmatter schema validity
3. Log integrity check result with timestamp

See `integrity-checks.md`.

---

## Restore Procedure

See `restore-procedures.md`.

In case of vault corruption:
1. Identify last known-good git commit
2. `git checkout <commit> -- forge-vault/`
3. Run integrity check on restored vault
4. Resume pipeline from last clean state

---

## Testing

Restore drills scheduled: monthly (manually triggered).
Results logged in `forge-vault/backups/restore-tests/`.
