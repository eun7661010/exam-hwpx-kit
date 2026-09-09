# Troubleshooting

[한국어](troubleshooting.ko.md)

## `absolute-asset-path` or `asset-path-escape`

Move the image below the JSON directory and use a relative path such as
`assets/chart.png`. Do not suppress this rule with a machine-specific path.

## `embedded-choice-marker`

Store only choice text. The renderer adds `①` through `⑤`. Removing the marker
from JSON prevents duplicated labels and keeps the source renderer-neutral.

## `keep-together-overflow-risk`

Shorten or split the question, reduce large images or support boxes, or set
`keep_together` to `false` after reviewing the trade-off. Raising
`max_lines_per_column` only changes the static risk threshold; it does not create
more space on the page.

## `invalid-json`

The file is not valid JSON or could not be read. A UTF-8 byte-order mark, which Notepad
and Windows PowerShell 5 `Out-File` add by default, is accepted. A UTF-16 file, a
trailing comma, or a comment still fails: save as UTF-8 and fix the syntax first.

## `schema`

A field is missing, has the wrong type, or is unknown. The path in the message points
to the exact location, for example `$.blocks[1].choices[0]`. Blank strings are rejected
everywhere, including individual choices.

## `duplicate-block-id`, `duplicate-question-number`, `duplicate-asset-id`

Block IDs, question numbers, and asset IDs must be unique within one document. Rename
or renumber; the audit relies on stable IDs.

## `question-order` (warning)

Question numbers are not ascending. Generation continues, but reorder the blocks unless
the order is intentional.

## `duplicate-passage-reference`, `missing-passage-question`, `passage-order`, `missing-question`

A passage lists the same question twice, references an ID that does not exist, or
appears after a question it references. Place the passage before its questions and list
each question once.

## `missing-image-reference`

A question references an image ID that is not declared in `assets`. Add the asset or
fix the ID.

## `unsupported-image-format`, `missing-asset-file`, `image-signature-mismatch`

Only `.png`, `.jpg`, and `.jpeg` are accepted, the file must exist below the JSON
directory, and its bytes must match the extension. A renamed WebP or SVG fails the
signature check; re-export the image as PNG or JPEG.

## `orphan-asset` (warning)

An asset is declared but no question uses it, so it is not embedded. Remove it or
reference it from a question.

## `unsafe-control-character`

The text contains a control character that XML forbids, such as U+0000 or U+001B. It
usually arrives through copy-and-paste; delete it in the source.

## The structural audit passes but the page looks wrong

Package and content integrity are not visual rendering. Export pages with your
trusted office suite, verify the required fonts, and follow
[`visual-regression.md`](visual-regression.md).

## Korean text is present but line breaks differ

Font substitution and office-suite layout engines affect line breaks. Freeze the
renderer, OS, font files, and export settings when visual stability matters.

## `visual-check` says the extra is missing

Install the optional dependency:

```bash
python -m pip install "exam-hwpx-kit[visual]"
```
