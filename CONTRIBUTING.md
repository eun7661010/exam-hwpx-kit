# Contributing

Thank you for improving `exam-hwpx-kit`. Small fixes, new validation rules,
cross-platform reports, documentation, and accessibility improvements are welcome.

## Before opening a pull request

1. Search existing issues and describe the user-visible problem.
2. Add or update a synthetic fixture that reproduces it.
3. Keep HWPX format work in `python-hwpx`; keep this repository focused on exam
   contracts, domain layout, and source-to-output integrity.
4. Update the JSON Schema and documentation when the public contract changes.
5. Run the complete local gate.

```bash
python -m pip install -e ".[dev]"
python tools/generate_synthetic_assets.py
python tools/export_schema.py
ruff check .
ruff format --check .
mypy src
pytest --cov=exam_hwpx_kit --cov-report=term-missing
python -m build
twine check dist/*
git diff --exit-code
```

## Fixture safety rules

Only submit content created specifically for this repository. Do not submit:

- Student, parent, teacher, employee, or customer data
- Real tests, passages, questions, answer sheets, or proprietary templates
- Organization names, logos, watermarks, internal hostnames, or service IDs
- Personal absolute paths, home directory names, API keys, tokens, cookies, or `.env` files
- Images, fonts, or documents without clear redistribution permission

Describe how every binary fixture was made in a nearby `NOTICE.md`. Prefer a
deterministic generator script. A reviewer may remove or reject any fixture whose
origin cannot be verified.

## Contract changes

The checked-in JSON Schema is generated from `ExamPaper`. A pull request that
changes the model must run `python tools/export_schema.py` and include the schema
diff. Breaking meaning or new required fields need a new `schema_version` and a
migration note.

Stable issue codes and CLI exit codes are public API. Rename them only with a
documented compatibility plan.

## HWPX changes

Do not write OWPML XML directly in this project. Use public `python-hwpx` APIs.
Reading generated XML for an audit is acceptable when no public observation API
exists, but the code must not mutate it.

Visual changes need:

- A structural test
- A synthetic HWPX example
- Renderer, OS, font, and export details for any PNG baseline
- An explicit statement when Hancom Office was not tested

## Commit and review scope

Keep pull requests focused. Explain what failed before, what the new invariant is,
and which test proves it. Contributors certify their work under Apache-2.0 by
submitting it; no separate contributor license agreement is required.
