# Studio Internationalization

## Supported locales

Studio 2.0 supports `en-US` and `zh-CN` in one Repository Review Workbench.
There is no separate Chinese page and no parallel legacy Studio implementation.

Locale selection is browser-local:

1. Use the valid value stored under `reposense.studio.locale`.
2. Otherwise, use `zh-CN` when `navigator.language` starts with `zh`.
3. Use `en-US` for every other language or when browser language is unavailable.

Changing locale updates the current view immediately. It does not rerun an
analysis or write locale data to a run, API payload, cookie, or server setting.

## Translation contract

Keys use stable semantic names such as `nav.home`, `pipeline.scanning_facts`,
and `workbench.transactions`. English is the fallback catalog. Missing keys do
not render JavaScript `undefined` or `null`; local development logs a warning.

To contribute a translation:

1. Add the English key to `webui/studio/locales/en-US.js`.
2. Add the `zh-CN` value to `webui/studio/locales/zh-CN.js`.
3. Preserve `{name}` parameter names across locales.
4. Do not put HTML fragments in locale dictionaries.
5. Run the i18n, Workbench, privacy, and packaging tests.
6. Check both locales at 1440 x 900 and a narrow viewport.

User-facing artifact names and descriptions resolve from `artifact_id`. The
server-provided English values remain safe fallbacks.

## Stable data boundary

Localization does not change API or artifact identifiers. Profile IDs, pipeline
statuses, Review Decision values, artifact IDs, categories, formats, audiences,
Rule IDs, Pattern IDs, CLI commands, JSON fields, and filenames remain stable
English identifiers.

Studio does not translate raw Markdown reports, JSON payloads, Context Pack
paths, CLI output, Pattern IDs, or Rule IDs.

## Product surfaces

- Studio 2.0 is the only routed Studio page and provides the bilingual workbench.
- `report.html` remains a generated, self-contained analytical report.
- Learn remains a generated learning view.
- Context Pack REVIEW remains the constrained human and AI handoff.

These surfaces have different responsibilities and are not duplicate Studio
implementations. Studio remains a read-only view of static-analysis evidence and
does not prove that a repository is secure or correct.
