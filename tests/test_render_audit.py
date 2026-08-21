from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from hwpx import HwpxDocument

from exam_hwpx_kit.audit import audit_hwpx
from exam_hwpx_kit.render import RenderError, build_document, create_template, render_exam


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


def test_template_refuses_to_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "template.hwpx"
    output.write_bytes(b"keep me")
    with pytest.raises(RenderError, match="덮어쓰지"):
        create_template(output)
    assert output.read_bytes() == b"keep me"
