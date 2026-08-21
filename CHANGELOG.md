# Changelog

All notable changes are documented here. This project follows Semantic Versioning
while the public contract remains pre-1.0.

## [0.1.0] - 2026-08-21

### Added

- Versioned `exam-hwpx-kit/v1` JSON Schema and strict Pydantic model
- Passage, question, choice, points, support-box, and image asset blocks
- Relative asset sandbox, duplicate and reference checks, control-character gate,
  and conservative keep-together overflow-risk check
- A4 one- and two-column HWPX generation through public `python-hwpx` APIs
- Package, editor-open-safety, ID, source-text, image-count, and column audit
- Privacy-minimized SHA-256 render receipt
- Renderer-neutral PNG visual comparison command
- Synthetic JSON, PNG, and template-generation workflow
- Windows, macOS, and Ubuntu CI for Python 3.10 and 3.13
- UTF-8 CLI output fallback for Windows shells that expose a non-Korean code page

[0.1.0]: https://github.com/eun7661010/exam-hwpx-kit/releases/tag/v0.1.0
