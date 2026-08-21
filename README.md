# exam-hwpx-kit

[![CI](https://github.com/eun7661010/exam-hwpx-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/eun7661010/exam-hwpx-kit/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/eun7661010/exam-hwpx-kit)](https://github.com/eun7661010/exam-hwpx-kit/releases)
[![Python](https://img.shields.io/badge/python-3.10--3.13-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

**Turn structured exam JSON into a Korean two-column HWPX worksheet, then prove
that the generated file still contains the expected questions, choices, boxes,
images, and layout declaration.**

[한국어 문서](README.ko.md)

## The problem

Exam content often starts as JSON, a database row, or an AI-generated draft, but
HWPX generation is usually handled by one-off scripts. A missing image, duplicate
question number, unsafe local path, broken choice marker, or silently dropped
paragraph may only be noticed after someone opens the document.

`exam-hwpx-kit` puts a small, testable contract around that workflow:

```text
exam JSON + relative assets
          │
          ▼
  schema + semantic validation
          │
          ▼
  python-hwpx authoring API
          │
          ▼
 two-column .hwpx + receipt
          │
          ▼
 package, ID, text, image, and column audit
```

It is intended for teachers, assessment-content teams, education developers, and
AI agents that need a deterministic JSON-to-HWPX exam generator without writing
OWPML XML by hand.

## What it catches

- Duplicate block IDs, question numbers, and asset IDs
- Passage references to missing or earlier questions
- Missing, absolute, escaping, or unsupported image paths
- PNG/JPEG files whose content does not match the declared extension
- Image references with no asset and assets used by no question
- Choice text that already contains circled-number markers
- XML-forbidden control characters before any HWPX is written
- A keep-together question that is too large for the configured column budget
- Generated HWPX packages that fail package, editor-open-safety, or ID checks
- Questions, choices, passage text, boxes, images, or column settings lost after generation

## Three-minute quick start

Python 3.10–3.13 is supported on Windows, macOS, and Linux.

```bash
git clone https://github.com/eun7661010/exam-hwpx-kit.git
cd exam-hwpx-kit
python -m venv .venv
python -m pip install -e .

exam-hwpx validate examples/synthetic-exam.json
exam-hwpx render examples/synthetic-exam.json synthetic-exam.hwpx
exam-hwpx audit examples/synthetic-exam.json synthetic-exam.hwpx
```

Expected output:

```text
검증 통과: 오류 0개, 경고 0개
생성 완료: synthetic-exam.hwpx (문항 2개, 이미지 1개)
감사 통과
```

`render` writes `synthetic-exam.hwpx.receipt.json` next to the document. The
receipt contains SHA-256 hashes, counts, validation results, and audit results. It
stores file names, not absolute source or output paths.

The bundled example and image are generated synthetic fixtures. They contain no
student data, copyrighted exam passages, organization branding, or private
template.

You can inspect the generated [synthetic HWPX output](examples/synthetic-output.hwpx)
and [blank synthetic template](examples/synthetic-template.hwpx) without running
the CLI first.

## Input and output

A minimal input looks like this:

```json
{
  "schema_version": "exam-hwpx-kit/v1",
  "title": "Synthetic Reading Practice",
  "layout": { "columns": 2 },
  "assets": [],
  "blocks": [
    {
      "type": "question",
      "id": "q1",
      "number": 1,
      "stem": "Which statement follows from the synthetic passage?",
      "choices": ["Choice A", "Choice B"],
      "keep_together": true
    }
  ]
}
```

The full contract supports:

- One- or two-column A4 layout with configurable margins and column gap
- Flowing passage blocks linked to one or more question IDs
- Questions with two to five choices and optional points
- Small support boxes such as `<보기>`
- Relative PNG and JPEG assets with alt text and display width
- Keep-together intent and a conservative pre-render overflow-risk budget

See the checked-in [JSON Schema](src/exam_hwpx_kit/schemas/exam-paper.v1.schema.json)
and [schema guide](docs/schema.md).

## Commands

| Command | Purpose | Exit code |
|---|---|---:|
| `exam-hwpx validate INPUT` | Validate schema, cross-references, paths, assets, and layout risk | `0` valid, `1` invalid |
| `exam-hwpx render INPUT OUTPUT` | Validate, generate HWPX, audit it, and write a receipt without overwriting existing files | `0` success, `1` blocked |
| `exam-hwpx audit INPUT OUTPUT` | Compare an existing HWPX with its source JSON | `0` match, `1` mismatch |
| `exam-hwpx template OUTPUT` | Create a content-free synthetic A4 HWPX starting point | `0` success |
| `exam-hwpx visual-check BASELINE CURRENT` | Compare trusted renderer PNG pages | `0` within threshold, `1` regression |

Add `--json` to `validate`, `render`, `audit`, or `visual-check` for stable
machine-readable output. Install `exam-hwpx-kit[visual]` to use `visual-check`.

## Design boundary

This project is a thin exam-content layer. It delegates HWPX package creation,
format-native paragraphs, tables, pictures, columns, and package checks to the
Apache-2.0 [`python-hwpx`](https://github.com/airmang/python-hwpx) project.

[`python-hwpx-automation`](https://github.com/airmang/python-hwpx-automation)
already offers Markdown-to-existing-form exam composition and renderer-assisted
question-split measurement. `exam-hwpx-kit` does not reimplement that workflow.
It adds a versioned JSON contract, asset sandbox, richer question blocks,
preflight integrity rules, a from-scratch synthetic document path, and a
source-to-output receipt. The two projects are complementary.

## Verification levels

The word “verified” is intentionally specific:

1. **Input verified** means the JSON schema, semantic rules, paths, and assets passed.
2. **Structure verified** means the HWPX package, editor-open-safety, shared IDs,
   declared columns, text, and image counts passed.
3. **Visually compared** means PNG pages exported by a trusted external renderer
   were compared with `visual-check`.
4. **Opened in Hancom Office** is not claimed unless you perform that check in your
   own environment.

`python-hwpx` provides strong format-native validation, but structural checks are
not a pixel-perfect rendering oracle. See [visual regression](docs/visual-regression.md).

## Privacy and security

The CLI does not call an LLM, upload documents, or use network services. Asset
paths must be relative to the JSON file and remain beneath its directory after
resolution. Receipts omit absolute paths and retain only file names and hashes.

The tool does not decide whether your source material is lawful, licensed, or safe
to publish. Do not put student records, answer sheets, credentials, private exam
content, or third-party copyrighted passages in a public repository. Read the
[security model](docs/security-model.md) and [security policy](SECURITY.md).

## Development

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
```

CI runs the test and example workflow on Windows, macOS, and Ubuntu with Python
3.10 and 3.13. See [CONTRIBUTING.md](CONTRIBUTING.md) for safe fixture and pull
request rules.

## Non-goals and current limits

- It is not a general HWPX editor, renderer, OCR system, or question generator.
- It does not provide answer-key secrecy, DRM, digital signatures, or exam security.
- Static overflow risk is conservative; actual page and column overflow requires a
  trusted renderer and visual inspection.
- Support boxes use a simple one-cell table. Long passages remain flowing body text.
- Version 0.1 supports PNG and JPEG images, plain text passages, and plain text choices.
- Font availability and final line breaks vary by operating system and office suite.

## License and provenance

Apache License 2.0. No code, template, passage, question, or asset from a private
project is included. See [NOTICE](NOTICE) for dependencies and synthetic fixture
provenance.
