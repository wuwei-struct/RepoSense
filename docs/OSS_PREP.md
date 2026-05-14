# OSS Preparation Notes

This document defines open-source preparation boundaries for RepoSense.

## License Layering Guidance

Recommended structure:

- Code: Apache-2.0 or MIT (final choice by maintainers).
- Documentation and concept maps: CC BY 4.0.
- Case library data: keep source attribution and minimal-necessary excerpts.

## Third-Party Repository Case Data Boundary

When building/maintaining cases from external repositories:

- Store only minimal necessary snippets.
- Keep `repo_ref` and provenance metadata.
- Do not copy large source sections.
- Be conservative on redistributability and licensing compatibility.

## Open-Source Release Checklist

Before release/public sync:

1. README first screen explains value, boundary, and quickstart.
2. Demo command runs and produces expected artifacts.
3. Known failing tests are documented explicitly.
4. Artifact paths and contracts are stable.
5. No secrets/private tokens/private paths are leaked.
6. Machine-specific assumptions are documented or removed.

## Trust Boundary Reminder

RepoSense is evidence-first and deterministic by design. AI outputs are derived artifacts, not truth source replacements.
