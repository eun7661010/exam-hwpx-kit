# Visual regression

HWPX package validation cannot prove that two office suites will produce the same
line breaks or page pixels. `visual-check` deliberately accepts PNG pages rather
than pretending to be an HWPX renderer.

## Recommended workflow

1. Generate the HWPX from a frozen JSON fixture.
2. Open and export it with one trusted office renderer and fixed fonts.
3. Save pages as `page-001.png`, `page-002.png`, and so on in a baseline folder.
4. Repeat with the candidate version into a current folder.
5. Compare both folders.

```bash
python -m pip install -e ".[visual]"
exam-hwpx visual-check baseline-pages current-pages \
  --max-changed-pixel-ratio 0.001 \
  --pixel-delta-threshold 8
```

PowerShell uses a backtick instead of the shell continuation shown above, or the
command can be written on one line.

The comparison requires identical page names and dimensions. A pixel counts as
changed when its grayscale delta exceeds the threshold. A page fails when its
changed-pixel ratio exceeds the configured limit.

## What to record with a baseline

- Renderer name and exact version
- Operating system and version
- Installed font names and versions
- Export resolution and color mode
- Source JSON SHA-256 and generated HWPX SHA-256
- The person or CI job that accepted the baseline

Do not commit a rendered page if it contains real students, copyrighted exam
material, private branding, or a font whose image redistribution is restricted.

## Interpretation

A passing image comparison means only that the supplied raster pages stayed
within the threshold. It does not certify the HWPX standard, accessibility,
correct answers, or legal right to use the content.
