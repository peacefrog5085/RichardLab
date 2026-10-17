# Security Policy

## Supported code

Security fixes target the current default branch. Historical snapshots and local experiment artifacts are not supported releases.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for this repository. Do not place credentials, exploit details, private host reports, or personal data in a public issue. Revoke and rotate any exposed credential immediately; deleting a file is not sufficient.

## Integration policy

External integrations are disabled and unverified by default. Read access must use the minimum provider scopes. Every external write requires an explicit, exact-scope, unexpired approval and post-action verification. Production deployment, permission expansion, destructive changes, and Git history rewriting require separate operator confirmation.

See `docs/security/THREAT_MODEL.md` and `docs/integrations/BASELINE_AND_DEPLOYMENT.md` for the current controls and residual risks.
