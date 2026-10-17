# RichardLab Echo integration threat model

Status: baseline design, 2026-10-17. No registry entry is evidence of a working connection.

## Assets and trust boundaries

Protected assets are service credentials, research data, source code, deployment settings, user communications, audit evidence, and local host details. Trust boundaries exist at user input, retrieved documents, model output, connector responses, approval decisions, environment variables, CI, logs, and every external service API.

Model output and connector content are untrusted data. They never authorize an action. The integration gateway is the policy boundary; adapters may not bypass it.

## STRIDE and abuse cases

| Threat | Abuse case | Required control |
|---|---|---|
| Spoofing | forged operator or connector identity | provider authentication plus recorded approving actor; identity integration still pending |
| Tampering | capability or approval scope altered | reviewed registry, exact operation/integration/capability match, protected branch |
| Repudiation | operator denies an external write | timestamped provenance events containing actor and operation ID |
| Information disclosure | token, PII, or host details enter logs | recursive redaction, secret scanning, report privacy check, data minimization |
| Denial of service | unbounded agent/tool loop or connector request | adapter timeouts, quotas, rate limits, and loop limits required before enablement |
| Elevation of privilege | read connector performs a write | read-only default and explicit per-capability allowlist plus approval gate |

Additional abuse cases include prompt injection requesting a tool call, replaying an old approval, using an approval for another operation, enabling an unverified connector, and exposing an administrative endpoint. The gateway rejects missing, expired, or mismatched approvals and disabled/unverified capabilities. This change creates no public or administrative endpoint.

## Residual risk and enablement gates

The approval object is an in-process policy primitive, not yet a cryptographically signed identity assertion. Before any live connector is enabled, add provider-specific authentication, server-side approval persistence, replay protection, timeouts, response validation, rate limiting, tenant isolation, and an adapter test against a non-production account. Production deployment and permission expansion require separate explicit confirmation.
