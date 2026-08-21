# Architecture

`exam-hwpx-kit` separates exam-domain decisions from HWPX format mechanics.

```text
ExamPaper model
 ├─ JSON Schema and Pydantic field validation
 ├─ semantic references and duplicate checks
 ├─ relative asset sandbox
 └─ conservative keep-together risk estimate
             │
             ▼
       domain renderer
 ├─ passage stays in flowing paragraphs
 ├─ question paragraphs receive keep settings
 ├─ support boxes use short one-cell tables
 └─ pictures and columns use python-hwpx APIs
             │
             ▼
        HWPX auditor
 ├─ package and editor-open-safety checks
 ├─ shared-resource ID integrity
 ├─ exact normalized source-text order comparison
 ├─ source-to-package image hash comparison
 ├─ column-declaration comparison
 └─ privacy-minimized receipt
```

## Dependency boundary

The package imports public `python-hwpx` APIs for document creation, page setup,
paragraph formatting, tables, pictures, persistence, package validation, and ID
integrity. It does not produce OWPML XML or copy `python-hwpx` source.

The auditor reads generated section XML only to observe the declared column count
and the image references used by the document. It does not write or mutate XML.
Malformed or unsafe package data becomes a failed audit report instead of being
reparsed or surfaced as an unhandled exception.

## Failure policy

Validation is fail-closed. `render` does not start if the source report contains an
error. After saving, the file is reopened and audited. If the audit fails, the
new output is removed and no successful receipt is returned.

Warnings, such as an unused asset, do not block generation. Errors have stable
codes suitable for CI policy.

## Why passages are not tables

Long passages need normal document flow across columns and pages. Putting a whole
passage inside a one-cell table can create a non-splittable container. Only short
support boxes use a one-cell table. Questions and their choices use paragraph
keep settings so the editor has an explicit cohesion hint without trapping all
content inside a table.
