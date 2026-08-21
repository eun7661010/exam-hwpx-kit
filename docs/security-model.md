# Security and privacy model

## Protected boundaries

- Asset paths must be relative to the JSON file.
- Resolved asset paths must stay beneath the JSON directory.
- Missing files, unsupported image extensions, and unsafe control characters block generation.
- Receipts contain base file names and hashes, not absolute input or output paths.
- The CLI performs no network request, document upload, telemetry, or LLM call.
- Examples and generated assets are synthetic and reproducible from checked-in scripts.

## Outside the threat model

- Detecting every kind of personal information inside prose or pixels
- Determining copyright ownership or permission to redistribute input content
- Antivirus or malware scanning of image files
- Hiding answer keys, encrypting documents, DRM, digital signatures, or exam delivery security
- Pixel-perfect rendering or a guarantee that a specific office version opens the file
- Protecting a system that runs the CLI on an already compromised host

Treat all exam JSON and images as sensitive until their origin and publication
rights are known. Run secret and personal-data scans before publishing a fixture.

## Reporting a vulnerability

Use GitHub private vulnerability reporting rather than a public issue when a
report contains exploit details, private documents, or personal information. See
[`SECURITY.md`](../SECURITY.md).
