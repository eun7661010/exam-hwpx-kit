# Exam JSON schema v1

The canonical machine-readable contract is
[`exam-paper.v1.schema.json`](../src/exam_hwpx_kit/schemas/exam-paper.v1.schema.json).
`tools/export_schema.py` regenerates it from the Pydantic model. CI regenerates the
file and rejects an uncommitted difference.

## Root fields

| Field | Required | Meaning |
|---|---:|---|
| `schema_version` | yes | Must be `exam-hwpx-kit/v1`. |
| `title` | yes | Document title, 1–200 characters. |
| `layout` | no | A4 margins, one or two columns, gap, and static line budget. |
| `assets` | no | Relative PNG/JPEG images. Asset IDs must be unique. |
| `blocks` | yes | Ordered passage and question blocks. |

Unknown fields are rejected so a typo cannot be silently ignored.

## Passage block

A passage has an `id`, visible `label`, flowing `text`, and `question_ids`. Every
referenced question must exist and appear after the passage. A question can be
referenced by more than one passage only if your own workflow permits it; v1 does
not prohibit cross-passage reuse.

## Question block

A question has a stable `id`, positive integer `number`, `stem`, two to five raw
choice strings, optional `points`, support `boxes`, `image_ids`, and a
`keep_together` intent. Do not prefix choices with `①` through `⑤`; the renderer
adds those markers exactly once.

## Assets

Asset paths are resolved from the directory that contains the JSON file. Absolute
Windows and POSIX paths are rejected. The resolved path must remain below that
directory, including after symlink resolution. Supported extensions are `.png`,
`.jpg`, and `.jpeg`.

The `alt` field is required even though HWPX v0.1 does not yet write it into the
picture object. Keeping it in the source contract prevents inaccessible source
data from being lost and leaves room for a future format-native mapping.

## Static overflow risk

`max_lines_per_column` is not a measured page height. It is a deterministic,
conservative budget used to catch obviously oversized keep-together questions
before generation. Font metrics and actual pagination require a trusted renderer.

## Versioning

Adding a required field or changing existing semantics requires a new
`schema_version`. New optional fields may be added only when older consumers can
reject them clearly under the existing `extra=forbid` behavior. Version migrations
must be explicit; the CLI never guesses.
