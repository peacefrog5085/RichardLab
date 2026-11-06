# RichardLab Echo 777

Echo 777 is a subproject of [peacefrog5085/RichardLab](https://github.com/peacefrog5085/RichardLab) for evidence-based research, investigation, development, and operator-controlled automation. The selected base is recorded in [current state](CURRENT_STATE.md). Follow [repository security policy](../../SECURITY.md).

## Resume

1. Read this file and the applicable operating instructions.
2. From the checkout, run `git rev-parse --show-toplevel`, `git branch --show-current`, `git rev-parse HEAD`, and `git --no-optional-locks status --short --branch --untracked-files=all`.
3. Read [latest handoff](SESSION_HANDOFF.md), [current state](CURRENT_STATE.md), and [next actions](NEXT_ACTIONS.md).
4. Compare repository, branch, commit, and working-tree claims with live Git and inspect relevant files. If a handoff differs, report both values, mark the handoff stale for the affected claims, and reconcile before relying on them.
5. Identify unfinished work and pending approvals. Summarize verified state, discrepancies, and the next authorized action. Stop at any approval boundary.

For ChatGPT or Work without checkout access, the operator can supply sanitized copies of identity, current state, and handoff with the handoff ID and commit. Such a session can draft a new handoff. A session with checkout access reconciles that draft against evidence before updating the canonical record.

## Knowledge rules

- **VERIFIED** requires inspectable evidence, a revision or date, and a statement of what the evidence establishes.
- **PROVISIONAL** covers claims awaiting evidence or review. An explicit evidence review is required for promotion. Chat summaries cannot prove implementation.
- **REJECTED** preserves a contradicted claim with its reason and evidence.
- Label synthetic and simulated data explicitly. Keep credentials, private account contents, and sensitive personal information out of project records unless explicitly authorized with appropriate safeguards.
