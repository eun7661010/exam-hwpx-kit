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

_PARAGRAPH_NS = "http://www.hancom.co.kr/hwpml/2011/paragraph"
_CHOICE_MARKS = "①②③④⑤"


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
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _column_counts(path: Path) -> list[int]:
    counts: list[int] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.startswith("Contents/section") or not name.endswith(".xml"):
                continue
            root = ET.fromstring(archive.read(name))
            for element in root.iter():
                if element.tag == f"{{{_PARAGRAPH_NS}}}colPr":
                    value = element.get("colCount") or element.get("count")
                    if value and value.isdigit():
                        counts.append(int(value))
    return counts


def _expected_text(exam: ExamPaper) -> list[tuple[str, str]]:
    expected: list[tuple[str, str]] = [("title", exam.title)]
    for block in exam.blocks:
        if block.type == "passage":
            expected.extend(
                (
                    (f"passage-label:{block.id}", block.label),
                    (f"passage:{block.id}", block.text),
                )
            )
            continue
        points = f" ({block.points}점)" if block.points is not None else ""
        expected.append((f"question:{block.id}", f"{block.number}. {block.stem}{points}"))
        expected.extend(
            (f"box:{block.id}:{index}", f"{box.label} {box.text}")
            for index, box in enumerate(block.boxes)
        )
        expected.extend(
            (f"choice:{block.id}:{index}", f"{_CHOICE_MARKS[index]} {choice}")
            for index, choice in enumerate(block.choices)
        )
    return expected


def _normalize(text: str) -> str:
    return " ".join(text.split())


def audit_hwpx(
    exam: ExamPaper,
    output_path: Path,
    *,
    source_root: Path | None = None,
) -> AuditReport:
    """Compare one HWPX against its source exam without a rendering oracle."""

    checks: list[AuditCheck] = []
    if not output_path.is_file():
        return AuditReport(
            ok=False,
            output_sha256="",
            checks=(AuditCheck(name="file", ok=False, detail="HWPX 파일을 찾을 수 없습니다."),),
        )

    try:
        package = validate_package(output_path)
        checks.append(AuditCheck(name="package", ok=package.ok, detail="HWPX 패키지 구조 검사"))
        open_safety = validate_editor_open_safety(output_path)
        checks.append(
            AuditCheck(name="open-safety", ok=open_safety.ok, detail="편집기 열림 안전 검사")
        )
    except Exception as exc:  # pragma: no cover - third-party validator diagnostics
        checks.append(AuditCheck(name="package", ok=False, detail=f"패키지 검사 실패: {exc}"))
        return AuditReport(ok=False, output_sha256=_sha256(output_path), checks=tuple(checks))

    if not package.ok or not open_safety.ok:
        return AuditReport(ok=False, output_sha256=_sha256(output_path), checks=tuple(checks))

    try:
        doc = HwpxDocument.open(output_path)
        text = _normalize(doc.text.plain())
        integrity = check_id_integrity(doc)
        checks.append(
            AuditCheck(name="id-integrity", ok=integrity.ok, detail="공유 자원 참조 검사")
        )

        expected = _expected_text(exam)
        cursor = 0
        for name, value in expected:
            normalized = _normalize(value)
            position = text.find(normalized, cursor)
            checks.append(
                AuditCheck(
                    name=name,
                    ok=position >= 0,
                    detail="원본 텍스트가 기대 순서와 소속으로 HWPX 평문 계층에 보존됨",
                )
            )
            if position >= 0:
                cursor = position + len(normalized)

        canonical = _normalize(" ".join(value for _, value in expected))
        checks.append(
            AuditCheck(
                name="content-exact",
                ok=text == canonical,
                detail="전체 평문이 기대 내용·순서·개수와 정확히 일치함",
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
        if source_root is not None:
            try:
                assets = {asset.id: asset for asset in exam.assets}
                expected_hashes = [
                    _sha256((source_root / assets[image_id].path).resolve())
                    for question in exam.questions
                    for image_id in question.image_ids
                ]
                media = {item.item_id: item.href for item in doc.media.images}
                actual_hashes: list[str] = []
                with zipfile.ZipFile(output_path) as archive:
                    for reference in doc.media.picture_references():
                        item_id = reference.binary_item_id_ref
                        if item_id is None:
                            raise KeyError("picture reference has no binary item ID")
                        actual_hashes.append(
                            hashlib.sha256(archive.read(media[item_id])).hexdigest()
                        )
                checks.append(
                    AuditCheck(
                        name="image-content",
                        ok=actual_hashes == expected_hashes,
                        detail="이미지 순서와 원본 payload SHA-256이 일치함",
                    )
                )
            except (OSError, KeyError, zipfile.BadZipFile) as exc:
                checks.append(
                    AuditCheck(name="image-content", ok=False, detail=f"이미지 감사 실패: {exc}")
                )
    except Exception as exc:  # pragma: no cover - third-party parser diagnostics
        checks.append(AuditCheck(name="reopen", ok=False, detail=f"HWPX 재개봉 실패: {exc}"))

    try:
        counts = _column_counts(output_path)
        checks.append(
            AuditCheck(
                name="columns",
                ok=bool(counts) and counts[-1] == exam.layout.columns,
                detail=f"선언된 단 수 {counts or '없음'}, 기대값 {exam.layout.columns}",
            )
        )
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        checks.append(AuditCheck(name="columns", ok=False, detail=f"단 설정 검사 실패: {exc}"))
    return AuditReport(
        ok=all(check.ok for check in checks),
        output_sha256=_sha256(output_path),
        checks=tuple(checks),
    )
