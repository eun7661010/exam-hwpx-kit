"""Render validated exam IR through python-hwpx public authoring APIs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from hwpx import HwpxDocument
from pydantic import BaseModel, ConfigDict, ValidationError

from .audit import AuditReport, audit_hwpx
from .models import ExamPaper, PassageBlock, QuestionBlock
from .validation import ValidationReport, validate_exam

_CHOICE_MARKS = "①②③④⑤"


class RenderError(RuntimeError):
    """Raised before writing output when the exam contract is not satisfied."""


class RenderReceipt(BaseModel):
    model_config = ConfigDict(frozen=True)

    receipt_version: str
    created_at: str
    source_sha256: str
    output_sha256: str
    source_name: str
    output_name: str
    questions: int
    passages: int
    images: int
    columns: int
    validation: ValidationReport
    audit: AuditReport


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _paragraph_index(doc: HwpxDocument) -> int:
    return len(doc.paragraphs) - 1


def _keep(doc: HwpxDocument, index: int, *, with_next: bool) -> None:
    doc.styles.apply_paragraph_format(
        paragraph_index=index,
        keep_with_next=with_next,
        keep_lines=True,
        line_spacing_percent=150,
        spacing_after_pt=2,
    )


def _add_passage(doc: HwpxDocument, passage: PassageBlock) -> None:
    doc.add_paragraph(passage.label, inherit_style=False)
    doc.styles.apply_paragraph_format(
        paragraph_index=_paragraph_index(doc),
        keep_with_next=True,
        keep_lines=True,
        spacing_before_pt=5,
        spacing_after_pt=3,
        bottom_border=True,
    )
    # A passage remains flowing body text. It is intentionally not placed in a
    # one-cell table, which can become a non-splittable container in HWPX.
    for paragraph_text in passage.text.split("\n"):
        doc.add_paragraph(paragraph_text, inherit_style=False)
        doc.styles.apply_paragraph_format(
            paragraph_index=_paragraph_index(doc),
            keep_with_next=False,
            keep_lines=True,
            line_spacing_percent=160,
            spacing_after_pt=2,
        )


def _add_question(
    doc: HwpxDocument, question: QuestionBlock, assets: dict[str, tuple[Path, float]]
) -> None:
    points = f" ({question.points}점)" if question.points is not None else ""
    doc.add_paragraph(f"{question.number}. {question.stem}{points}", inherit_style=False)
    _keep(doc, _paragraph_index(doc), with_next=True)

    for box in question.boxes:
        table = doc.add_table(1, 1)
        table.set_cell_text(0, 0, f"{box.label}  {box.text}")
        _keep(doc, _paragraph_index(doc), with_next=True)

    for image_id in question.image_ids:
        image_path, width_mm = assets[image_id]
        image_format = "jpeg" if image_path.suffix.lower() in {".jpg", ".jpeg"} else "png"
        doc.add_picture(
            image_path.read_bytes(),
            image_format,
            width_mm=width_mm,
            align="CENTER",
        )
        _keep(doc, _paragraph_index(doc), with_next=True)

    for index, choice in enumerate(question.choices):
        doc.add_paragraph(f"{_CHOICE_MARKS[index]} {choice}", inherit_style=False)
        is_last = index == len(question.choices) - 1
        _keep(doc, _paragraph_index(doc), with_next=question.keep_together and not is_last)


def build_document(exam: ExamPaper, *, root: Path) -> HwpxDocument:
    """Build an in-memory HWPX document from already validated IR."""

    doc = HwpxDocument.new()
    margins = exam.layout.margins
    doc.page.setup(
        paper_size="A4",
        margin_top_mm=margins.top_mm,
        margin_bottom_mm=margins.bottom_mm,
        margin_left_mm=margins.left_mm,
        margin_right_mm=margins.right_mm,
        columns=exam.layout.columns,
        column_gap_mm=exam.layout.column_gap_mm,
    )
    doc.add_heading(exam.title, level=1)
    doc.styles.apply_paragraph_format(
        paragraph_index=_paragraph_index(doc),
        alignment="CENTER",
        keep_with_next=True,
        keep_lines=True,
        spacing_after_pt=8,
    )

    assets = {asset.id: ((root / asset.path).resolve(), asset.width_mm) for asset in exam.assets}
    for block in exam.blocks:
        if isinstance(block, PassageBlock):
            _add_passage(doc, block)
        elif isinstance(block, QuestionBlock):
            _add_question(doc, block, assets)
    return doc


def render_exam(
    exam: ExamPaper,
    *,
    source_path: Path,
    output_path: Path,
    receipt_path: Path | None = None,
) -> RenderReceipt:
    """Validate, render, audit, and write a privacy-minimized receipt."""

    receipt_path = receipt_path or output_path.with_suffix(output_path.suffix + ".receipt.json")
    if output_path.resolve() == receipt_path.resolve():
        raise RenderError("HWPX 출력 경로와 영수증 경로는 서로 달라야 합니다.")
    if output_path.exists():
        raise RenderError(f"기존 출력 파일을 덮어쓰지 않습니다: {output_path.name}")
    if receipt_path.exists():
        raise RenderError(f"기존 영수증 파일을 덮어쓰지 않습니다: {receipt_path.name}")

    try:
        source_bytes = source_path.read_bytes()
        source_payload = json.loads(source_bytes.decode("utf-8-sig"))
        source_exam = ExamPaper.model_validate(source_payload)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        raise RenderError(f"시험 JSON을 읽을 수 없습니다: {exc}") from exc
    if source_exam != exam:
        raise RenderError("전달된 입력 모델이 source_path의 시험 JSON과 일치하지 않습니다.")

    validation = validate_exam(source_exam, root=source_path.parent)
    if not validation.ok:
        raise RenderError("시험 JSON 검증에 실패하여 HWPX를 만들지 않았습니다.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = build_document(source_exam, root=source_path.parent)
    doc.save_to_path(output_path)
    audit = audit_hwpx(source_exam, output_path, source_root=source_path.parent)
    if not audit.ok:
        output_path.unlink(missing_ok=True)
        raise RenderError("생성된 HWPX가 내용 무결성 감사를 통과하지 못했습니다.")

    receipt = RenderReceipt(
        receipt_version="exam-hwpx-kit/receipt/v1",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        output_sha256=_sha256(output_path),
        source_name=source_path.name,
        output_name=output_path.name,
        questions=len(source_exam.questions),
        passages=len(source_exam.passages),
        images=sum(len(question.image_ids) for question in source_exam.questions),
        columns=source_exam.layout.columns,
        validation=validation,
        audit=audit,
    )
    receipt_path.write_text(
        json.dumps(receipt.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return receipt


def create_template(output_path: Path, *, columns: int = 2) -> None:
    """Create a synthetic, content-free A4 HWPX starting point."""

    if output_path.exists():
        raise RenderError(f"기존 출력 파일을 덮어쓰지 않습니다: {output_path.name}")
    doc = HwpxDocument.new()
    doc.page.setup(
        paper_size="A4",
        margin_top_mm=15,
        margin_bottom_mm=15,
        margin_left_mm=15,
        margin_right_mm=15,
        columns=columns,
        column_gap_mm=6,
    )
    doc.add_heading("Synthetic Exam Template", level=1)
    doc.add_paragraph("Replace this synthetic placeholder with validated exam content.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save_to_path(output_path)
