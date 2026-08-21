"""Post-render package and content-integrity audit."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from hwpx import HwpxDocument
from hwpx.tools.id_integrity import check_id_integrity
from hwpx.tools.package_validator import validate_editor_open_safety, validate_package
from pydantic import BaseModel, ConfigDict

from .models import ExamPaper


class AuditCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    ok: bool
    detail: str


class AuditReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool
    output_sha256: str
    checks: tuple[AuditCheck, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _column_counts(path: Path) -> list[int]:
    counts: list[int] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.startswith("Contents/section") or not name.endswith(".xml"):
                continue
            root = ET.fromstring(archive.read(name))
            for element in root.iter():
                if element.tag.rsplit("}", 1)[-1] == "colPr":
                    value = element.get("colCount") or element.get("count")
                    if value and value.isdigit():
                        counts.append(int(value))
    return counts


def audit_hwpx(exam: ExamPaper, output_path: Path) -> AuditReport:
    """Compare one HWPX against its source exam without a rendering oracle."""

    checks: list[AuditCheck] = []
    if not output_path.is_file():
        return AuditReport(
            ok=False,
            output_sha256="",
            checks=(AuditCheck(name="file", ok=False, detail="HWPX 파일을 찾을 수 없습니다."),),
        )

    package = validate_package(output_path)
    checks.append(AuditCheck(name="package", ok=package.ok, detail="HWPX 패키지 구조 검사"))
    open_safety = validate_editor_open_safety(output_path)
    checks.append(AuditCheck(name="open-safety", ok=open_safety.ok, detail="편집기 열림 안전 검사"))

    try:
        doc = HwpxDocument.open(output_path)
        text = " ".join(doc.text.plain().split())
        integrity = check_id_integrity(doc)
        checks.append(
            AuditCheck(name="id-integrity", ok=integrity.ok, detail="공유 자원 참조 검사")
        )

        expected: list[tuple[str, str]] = [("title", exam.title)]
        for passage in exam.passages:
            expected.extend(
                (
                    (f"passage-label:{passage.id}", passage.label),
                    (f"passage:{passage.id}", passage.text),
                )
            )
        for question in exam.questions:
            expected.append((f"question:{question.id}", f"{question.number}. {question.stem}"))
            expected.extend(
                (f"choice:{question.id}:{index}", choice)
                for index, choice in enumerate(question.choices)
            )
            expected.extend(
                (f"box:{question.id}:{index}", box.text) for index, box in enumerate(question.boxes)
            )
        for name, value in expected:
            normalized = " ".join(value.split())
            checks.append(
                AuditCheck(
                    name=name,
                    ok=normalized in text,
                    detail="원본 텍스트가 HWPX 평문 계층에 보존됨",
                )
            )

        actual_images = len(doc.media.picture_references())
        expected_images = sum(len(question.image_ids) for question in exam.questions)
        checks.append(
            AuditCheck(
                name="image-count",
                ok=actual_images == expected_images,
                detail=f"이미지 {actual_images}/{expected_images}",
            )
        )
    except Exception as exc:  # pragma: no cover - third-party parser diagnostics
        checks.append(AuditCheck(name="reopen", ok=False, detail=f"HWPX 재개봉 실패: {exc}"))

    counts = _column_counts(output_path)
    checks.append(
        AuditCheck(
            name="columns",
            ok=exam.layout.columns in counts,
            detail=f"선언된 단 수 {counts or '없음'}, 기대값 {exam.layout.columns}",
        )
    )
    return AuditReport(
        ok=all(check.ok for check in checks),
        output_sha256=_sha256(output_path),
        checks=tuple(checks),
    )
