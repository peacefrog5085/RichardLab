# Evidence index

## E-001 — Upstream base

**VERIFIED** — Read-only Git remote ref lookup and GitHub comparison. [Echo commit](https://github.com/peacefrog5085/RichardLab/commit/7e9ae40258ac65735fccd97f652115aca8d2fd7e) and [branch comparison](https://github.com/peacefrog5085/RichardLab/compare/master...codex/echo-plugin-security).

## E-002 — Upstream CI

**VERIFIED** — [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/39053754261) and [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/39053754251) succeeded on E-001. These runs cover the upstream commit.

## E-003 — October 23 demo

**VERIFIED** — Discovery observed an unborn `codex/echo-demo` branch with untracked files and no configured remote. Its adjacent artifact `RichardLab_Echo_Verification_Report.md`, dated 2026-10-23, records 189 passed in 17.81 seconds. This establishes the reported result. The exact revision behind that run remains **PROVISIONAL**.

## E-004 — Earlier pilot

**VERIFIED** — [Published GitHub pilot](https://github.com/peacefrog5085/RichardLab/commit/7c91f6b54d2067b3a8ff4a2338295e0601cfced9) and [master invocation fix](https://github.com/peacefrog5085/RichardLab/commit/4b0bc7977219b24b95ba79991b9ac6c35b5c811d). The historical local pilot checkout was clean at `a82e1a38de8cd4d8f7309691919ac91c292ed36e`. Its relationship to the published refs remains **PROVISIONAL** because GitHub did not resolve the local SHA.

## E-005 — Historical memory

**VERIFIED** — The local October 8 artifact `docs/RICHARDLAB_MIGRATION_REPORT.md` describes Basic Memory `main` and its historical archive map. Current service state is **PROVISIONAL**. Use the original archive records if separately authorized to inspect them.

## E-006 — Offline investigation CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `4b3a893b6e7c5d68322939350ef165c065da6018`. These results cover that revision. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42142106386) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42142106374)

## E-007 — Offline review CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `fa2da357c3c24fef38888e75d7825d5e090b668c`. These results cover that revision. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42143665134) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42143665066)

## E-008 — Offline check CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `1fef44addecd5f8d737d011ce80fe8bb403a2d2a`. These results cover that revision. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42145258774) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42145258765)

## E-009 — Offline review template CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `b3beeb6cde9a37c014f7fd063aa323ead136bced`. These results cover that revision. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42146272161) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42146272068)

## E-010 — Report packet digest CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `e12490c81ac01fff269713de776b7159e3c9c988`. These results cover that revision. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42149879552) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42149879521)

## E-011 — Offline report matching CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `de8441e47d10fd19c39f0ee2ca1b31e9c69f2226`. These results cover that revision. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42163033853) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42163033889)

## E-012 — Offline report verification CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `e3d98f822b97e2e4a97b1d8c7cbcddbd23b83ab5`. These results cover that revision. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42234444394) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42234444378)

## E-013 — Report mismatch diagnostic CI

**VERIFIED** — Both push workflows completed successfully on `codex/echo-plugin-security` at `2db5bd13c1eb32e1a120751fcc084fbe793da68d`. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42235804155) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42235803993)

## E-014 — Local investigation using real CI sources

**VERIFIED** — The local packet used exact excerpts from the two workflow definitions at the E-013 revision. The investigation establishes which commands the definitions configure. E-013 records their observed outcomes. The packet, draft, and report are under the ignored local directory `reports/echo-777-real-ci/`. The original report used the fixed “Synthetic evidence” label. The replay in `report-real.md` uses “Real evidence” and passed exact report verification. Human review is pending. [Integration security source](https://github.com/peacefrog5085/RichardLab/blob/2db5bd13c1eb32e1a120751fcc084fbe793da68d/.github/workflows/integration-security.yml) · [Report privacy source](https://github.com/peacefrog5085/RichardLab/blob/2db5bd13c1eb32e1a120751fcc084fbe793da68d/.github/workflows/report-privacy.yml)

## E-015 — Real-evidence label CI

**VERIFIED** — Both push workflows completed successfully on `codex/echo-plugin-security` at `c8bb8b03ead558c0e03405b65d2560628f55f295`. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42237362749) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42237362731)

## E-016 — Citation source path CI

**VERIFIED** — Both push workflows completed successfully on `codex/echo-plugin-security` at `cb7d89285343b6f6f6d10eaabdddf47063bef741`. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42238607431) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42238607488)

## E-017 — Citation line range CI

**VERIFIED** — Both push workflows completed successfully on `codex/echo-plugin-security` at `3735519c690d713c1d9e2e9b614685b4549a819d`. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42241419646) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42241419756)

## E-018 — Pinned source verification CI

**VERIFIED** — Both push workflows completed successfully on `codex/echo-plugin-security` at `2f5fa9a53d2fe7eaedb41b3b61c8b5204b5b5727`. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42248172778) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42248172505)

## E-019 — Source mismatch diagnostic CI

**VERIFIED** — Both push workflows completed successfully on `codex/echo-plugin-security` at `096e3984e875d7ce7296f53366dd662003c8b45f`. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42249950137) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42249950097)

## E-020 — Local Echo status API CI

**VERIFIED** — GitHub Actions recorded both push workflows as completed successfully on `codex/echo-plugin-security` at `cbd183799f12791e4c045aafb894d22d43e9c8a2`. These results cover the pushed revision of the local-only status API. [Integration security](https://github.com/peacefrog5085/RichardLab/actions/runs/42301729646) · [Report privacy](https://github.com/peacefrog5085/RichardLab/actions/runs/42301729711)
