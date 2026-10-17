# GitHub read-only capability evidence

Recorded: 2026-10-17

## Decision

Only the GitHub read capabilities exercised by the bounded pilot are classified as
`verified`. They remain disabled by default. GitHub write capabilities remain
disabled, unverified, and approval-gated.

Verified capability mappings:

| Registry capability | Evidence |
|---|---|
| `repository.read` | Repository metadata returned for `peacefrog5085/RichardLab` |
| `issues.read` | Issues endpoint returned results |
| `pull_requests.read` | Pull requests endpoint returned results |
| `checks.read` | The public repository's check-runs endpoint returned results; this is not evidence of a token-granted Checks permission |

## Runtime evidence

- Workflow: `GitHub read-only pilot`
- Run: https://github.com/peacefrog5085/RichardLab/actions/runs/39057031897
- Commit: `4b0bc7977219b24b95ba79991b9ac6c35b5c811d`
- Result: success
- Reported reads: metadata=true, pull_requests=5, issues=5, check_runs=3
- Reported safety counters: writes_attempted=0, token_logged=false
- Repository binding: `peacefrog5085/RichardLab`
- Workflow's built-in `GITHUB_TOKEN`: contents=read, metadata=read
- Checkout: `persist-credentials: false`

The pilot credential was supplied through the
`RICHARDLAB_GITHUB_READ_TOKEN` Actions secret and remained masked in logs.

## Permission-screen evidence

The operator supplied screenshots, reviewed on 2026-10-17, showing:

- token name: `RichardLab Echo Read Only`
- repository access restricted to `peacefrog5085/RichardLab`
- zero account permissions
- read-only repository permissions for Contents, Issues, Metadata, and Pull requests
- no Actions or Commit statuses permission
- expiration on 2026-11-16
- GitHub confirmation that the token update succeeded
- no token value displayed

The fine-grained personal-token permission selector did not offer a Checks
permission. The credential was not broadened with Actions or Commit statuses as
a substitute. Check-run visibility is therefore accepted only for this public
repository and must be re-evaluated before the repository becomes private.

The screenshots are intentionally not committed to the public repository. Do
not put a token value, partial token, authorization header, or private key in
this repository, an issue, a pull request, or an Actions artifact.

## Limits

A successful read pilot verifies that the listed read operations work. Because
no mutation was attempted, it does not prove that the credential lacks every
write permission. No write-denial probe will be performed merely to test this.

No production capability is activated by this evidence record. Activation,
credential expansion, write capability, report removal, and history rewrite
each require explicit confirmation.
