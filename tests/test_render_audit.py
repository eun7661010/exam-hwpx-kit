from __future__ import annotations

import json
import re
import shutil
import zipfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path

import pytest
from hwpx import HwpxDocument
from PIL import Image

from exam_hwpx_kit.audit import audit_hwpx
from exam_hwpx_kit.render import RenderError, build_document, create_template, render_exam


def rewrite_member(path: Path, member: str, transform: Callable[[bytes], bytes]) -> None:
    replacement = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(path) as source, zipfile.ZipFile(replacement, "w") as target:
        for info in source.infolist():
            payload = source.read(info.filename)
            target.writestr(info, transform(payload) if info.filename == member else payload)
    replacement.replace(path)


def test_build_document_has_two_columns_and_content(example_exam, example_path: Path) -> None:
    doc = build_document(example_exam, root=example_path.parent)
    text = doc.text.plain()
    assert example_exam.title in text
    assert "1." in text
    assert "①" in text
    assert len(doc.media.picture_references()) == 1


def test_render_reopens_and_writes_minimized_receipt(
    example_exam, example_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.hwpx"
    receipt = render_exam(example_exam, source_path=example_path, output_path=output)
    assert receipt.audit.ok
    assert receipt.validation.ok
    assert receipt.source_name == "synthetic-exam.json"
    assert receipt.output_name == "result.hwpx"
    assert "/" not in receipt.source_name and "\\" not in receipt.source_name
    assert "/" not in receipt.output_name and "\\" not in receipt.output_name
    reopened = HwpxDocument.open(output)
    assert "합성 독해 연습지" in reopened.text.plain()
    assert output.with_suffix(".hwpx.receipt.json").is_file()


def test_audit_detects_source_mismatch(example_exam, example_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "result.hwpx"
    render_exam(example_exam, source_path=example_path, output_path=output)
    changed = example_exam.model_copy(update={"title": "다른 제목"})
    report = audit_hwpx(changed, output)
    assert report.ok is False
    assert any(check.name == "title" and not check.ok for check in report.checks)


def test_audit_missing_file(example_exam, tmp_path: Path) -> None:
    report = audit_hwpx(example_exam, tmp_path / "missing.hwpx")
    assert report.ok is False
    assert report.output_sha256 == ""


def test_template_is_synthetic_and_valid(tmp_path: Path) -> None:
    output = tmp_path / "template.hwpx"
    create_template(output)
    with zipfile.ZipFile(output) as archive:
        assert "mimetype" in archive.namelist()
    doc = HwpxDocument.open(output)
    assert "Synthetic Exam Template" in doc.text.plain()


def test_render_refuses_to_overwrite_output(
    example_exam, example_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.hwpx"
    output.write_bytes(b"keep me")
    with pytest.raises(RenderError, match="덮어쓰지"):
        render_exam(example_exam, source_path=example_path, output_path=output)
    assert output.read_bytes() == b"keep me"


def test_render_rejects_receipt_path_equal_to_output(
    example_exam, example_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.hwpx"

    with pytest.raises(RenderError, match="서로 달라야"):
        render_exam(
            example_exam,
            source_path=example_path,
            output_path=output,
            receipt_path=output,
        )

    assert not output.exists()


def test_render_rejects_exam_that_does_not_match_source(
    example_exam, example_path: Path, example_payload: dict, tmp_path: Path
) -> None:
    source = tmp_path / "different.json"
    changed = {**example_payload, "title": "다른 합성 시험지"}
    source.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
    for asset in example_exam.assets:
        target = tmp_path / asset.path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(example_path.parent / asset.path, target)

    with pytest.raises(RenderError, match="일치하지"):
        render_exam(example_exam, source_path=source, output_path=tmp_path / "result.hwpx")


def test_audit_rejects_reordered_choices(example_exam, example_path: Path, tmp_path: Path) -> None:
    output = tmp_path / "result.hwpx"
    render_exam(example_exam, source_path=example_path, output_path=output)
    first, second = example_exam.questions[0].choices[:2]

    def swap(payload: bytes) -> bytes:
        text = payload.decode("utf-8")
        assert first in text and second in text
        text = text.replace(first, "__FIRST_CHOICE__", 1)
        text = text.replace(second, first, 1)
        return text.replace("__FIRST_CHOICE__", second, 1).encode("utf-8")

    rewrite_member(output, "Contents/section0.xml", swap)

    report = audit_hwpx(example_exam, output)

    assert report.ok is False
    assert any(check.name == "content-exact" and not check.ok for check in report.checks)


def test_audit_ignores_foreign_namespace_column_declaration(
    example_exam, example_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.hwpx"
    render_exam(example_exam, source_path=example_path, output_path=output)

    def spoof(payload: bytes) -> bytes:
        text = payload.decode("utf-8")
        changed, count = re.subn(
            r'<hp:colPr(?=[^>]*colCount="2")',
            '<evil:colPr xmlns:evil="urn:synthetic:evil"',
            text,
            count=1,
        )
        assert count == 1
        return changed.encode("utf-8")

    rewrite_member(output, "Contents/section0.xml", spoof)

    report = audit_hwpx(example_exam, output)

    assert report.ok is False
    assert any(check.name == "columns" and not check.ok for check in report.checks)


def test_audit_returns_failed_report_for_malformed_section(
    example_exam, example_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.hwpx"
    render_exam(example_exam, source_path=example_path, output_path=output)
    rewrite_member(output, "Contents/section0.xml", lambda _: b"<broken")

    report = audit_hwpx(example_exam, output)

    assert report.ok is False
    assert any(not check.ok for check in report.checks)


def test_audit_rejects_substituted_image_payload(
    example_exam, example_path: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.hwpx"
    render_exam(example_exam, source_path=example_path, output_path=output)
    with zipfile.ZipFile(output) as archive:
        image_member = next(name for name in archive.namelist() if name.startswith("BinData/"))
    replacement = BytesIO()
    Image.new("RGB", (2, 2), color=(255, 0, 0)).save(replacement, format="PNG")
    rewrite_member(output, image_member, lambda _: replacement.getvalue())

    report = audit_hwpx(example_exam, output, source_root=example_path.parent)

    assert report.ok is False
    assert any(check.name == "image-content" and not check.ok for check in report.checks)


def test_template_refuses_to_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "template.hwpx"
    output.write_bytes(b"keep me")
    with pytest.raises(RenderError, match="덮어쓰지"):
        create_template(output)
    assert output.read_bytes() == b"keep me"
