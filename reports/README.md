# Public report policy

Only reviewed, sanitized benchmark results and simulation outputs belong here.
Raw system scans belong in the ignored `private_reports/` directory. The scan
scripts save there with owner-only directory/file permissions and do not echo
the diagnostic contents into terminal logs.

Before sharing any report, remove usernames, hostnames, home-directory paths,
network addresses, MAC addresses, service/process inventories and credentials.
Retain hardware/software details only when needed to reproduce a benchmark.
Inspect image labels and metadata as well as text. Do not use `git add -f` to
publish raw diagnostics.

Enable the local pre-commit guard once per clone (requires Python 3):

```sh
git config core.hooksPath .githooks
```

If you already use custom Git hooks, integrate this check into them instead of
replacing their hooks path. The repository cannot enable hooks on other clones.

Run manually before committing:

```sh
python3 tools/check_report_privacy.py
```

The check reads staged/tracked content from the Git index, including files
already tracked despite ignore rules. It reports categories without printing
sensitive values. GitHub Actions runs the same check on pushes and pull requests.
It detects common patterns, not every secret or identifying detail; manual
review remains necessary. A push check runs after upload. Configure the
`report-privacy` check as required in branch rules to enforce it before merging.

The September raw system scan was removed from the current tree. The archived
benchmark was sanitized and its generator updated. Earlier commits and existing
clones can still contain the old data; this cleanup does not rewrite history.
