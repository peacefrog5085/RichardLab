# Plugin integration baseline and deployment plan

## Verified baseline (2026-10-17)

- Repository: `peacefrog5085/RichardLab`, local `master` initially at `c76e208`, three commits ahead of `origin/master`.
- Existing AI providers are configuration-driven; this review did not verify external credentials or successful provider calls.
- Existing security code scans common secret patterns, ignored sensitive filenames, Git history, network listeners, and repository state.
- CI previously enforced only report privacy. The integration security workflow adds tests, the read-only security audit, registry validation through tests, and report privacy checking.
- Historical experiment files under `reports/` remain tracked. They were not removed, rewritten, or published by this work. The privacy checker is the current disclosure gate.

## Capability registry

`ai/integrations/registry.json` is the source of declared connector capabilities. Every connector defaults to disabled, unverified, read-only, and approval-required for mutations. A declaration means “known to policy,” not “connected.”

To activate one connector in a later reviewed change:

1. Choose only the required read scopes in the provider console and document their exact names.
2. Store credentials in the deployment secret manager, never source control or logs.
3. Implement a narrow adapter with HTTPS, timeouts, response validation, bounded pagination, and generic errors.
4. Verify against a non-production account and add contract tests.
5. Mark only that connector verified and enabled. Keep access read-only.
6. For a write capability, add an exact approval workflow, idempotency/replay protection, and post-action verification before changing access to `read_write`.

## Review and deployment

1. Review the registry, threat model, CI, and tests as a pull request; compare against the three pre-existing local commits.
2. Run the full test suite and security workflow on the PR with no production secrets.
3. Merge without deploying connector credentials; behavior remains disabled by default.
4. Configure one non-production connector at a time and record evidence separately.
5. Request explicit confirmation before any production deployment, external write, credential provisioning, history rewrite, report removal, or permission expansion.

Rollback is additive: revert the integration commit or keep every registry entry disabled. No database migration or external state change is part of this changeset.
