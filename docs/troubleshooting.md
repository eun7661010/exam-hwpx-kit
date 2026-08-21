# Troubleshooting

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
