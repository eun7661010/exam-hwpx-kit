"""Fail-closed semantic and asset validation for exam specifications."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path, PureWindowsPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from .models import ExamPaper, QuestionBlock

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CHOICE_MARK_RE = re.compile(r"^[①②③④⑤]\s*")
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def _has_expected_image_signature(path: Path) -> bool:
    try:
        header = path.read_bytes()[:12]
    except OSError:
        return False
    if path.suffix.lower() == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    return header.startswith(b"\xff\xd8\xff")


class Issue(BaseModel):
    model_config = ConfigDict(frozen=True)

    severity: Literal["error", "warning"]
    code: str
    path: str
    message: str


class ValidationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool
    errors: int
    warnings: int
    issues: tuple[Issue, ...]

    @classmethod
    def from_issues(cls, issues: list[Issue]) -> ValidationReport:
        errors = sum(issue.severity == "error" for issue in issues)
        warnings = sum(issue.severity == "warning" for issue in issues)
        return cls(ok=errors == 0, errors=errors, warnings=warnings, issues=tuple(issues))


def _issue(severity: Literal["error", "warning"], code: str, path: str, message: str) -> Issue:
    return Issue(severity=severity, code=code, path=path, message=message)


def _duplicates(values: list[Any]) -> list[Any]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def _iter_strings(value: Any, path: str = "$") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, str):
        found.append((path, value))
    elif isinstance(value, dict):
        for key, child in value.items():
            found.extend(_iter_strings(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_iter_strings(child, f"{path}[{index}]"))
    return found


def _estimate_question_lines(question: QuestionBlock) -> int:
    text_lines = math.ceil(len(question.stem) / 28)
    choice_lines = sum(max(1, math.ceil(len(choice) / 24)) for choice in question.choices)
    box_lines = sum(2 + math.ceil(len(box.text) / 24) for box in question.boxes)
    image_lines = len(question.image_ids) * 12
    return 2 + text_lines + choice_lines + box_lines + image_lines


def validate_exam(exam: ExamPaper, *, root: Path) -> ValidationReport:
    """Validate cross-field rules and all asset references beneath *root*."""

    issues: list[Issue] = []
    payload = exam.model_dump(mode="json")

    for path, value in _iter_strings(payload):
        match = _CONTROL_RE.search(value)
        if match:
            issues.append(
                _issue(
                    "error",
                    "unsafe-control-character",
                    path,
                    f"XML에서 허용되지 않는 제어 문자 U+{ord(match.group()):04X}가 있습니다.",
                )
            )

    block_ids = [block.id for block in exam.blocks]
    for duplicate in _duplicates(block_ids):
        issues.append(_issue("error", "duplicate-block-id", "$.blocks", f"중복 ID: {duplicate}"))

    question_ids = [question.id for question in exam.questions]
    question_numbers = [question.number for question in exam.questions]
    for duplicate in _duplicates(question_numbers):
        issues.append(
            _issue("error", "duplicate-question-number", "$.blocks", f"중복 문항 번호: {duplicate}")
        )
    if question_numbers != sorted(question_numbers):
        issues.append(
            _issue("warning", "question-order", "$.blocks", "문항 번호가 오름차순이 아닙니다.")
        )

    question_positions = {block.id: index for index, block in enumerate(exam.blocks)}
    for passage_index, passage in enumerate(exam.passages):
        duplicate_refs = _duplicates(passage.question_ids)
        for duplicate in duplicate_refs:
            issues.append(
                _issue(
                    "error",
                    "duplicate-passage-reference",
                    f"$.passages[{passage_index}].question_ids",
                    f"같은 문항을 두 번 참조합니다: {duplicate}",
                )
            )
        for question_id in passage.question_ids:
            if question_id not in question_positions:
                issues.append(
                    _issue(
                        "error",
                        "missing-passage-question",
                        f"$.passages[{passage_index}].question_ids",
                        f"존재하지 않는 문항 ID: {question_id}",
                    )
                )
            elif question_positions[question_id] <= question_positions[passage.id]:
                issues.append(
                    _issue(
                        "error",
                        "passage-order",
                        f"$.passages[{passage_index}].question_ids",
                        f"지문이 참조 문항보다 먼저 나와야 합니다: {question_id}",
                    )
                )

    asset_ids = [asset.id for asset in exam.assets]
    for duplicate in _duplicates(asset_ids):
        issues.append(
            _issue("error", "duplicate-asset-id", "$.assets", f"중복 자산 ID: {duplicate}")
        )

    root = root.resolve()
    asset_map = {asset.id: asset for asset in exam.assets}
    for index, asset in enumerate(exam.assets):
        relative = Path(asset.path)
        if relative.is_absolute() or PureWindowsPath(asset.path).is_absolute():
            issues.append(
                _issue(
                    "error",
                    "absolute-asset-path",
                    f"$.assets[{index}].path",
                    "자산 경로는 JSON 파일을 기준으로 한 상대 경로여야 합니다.",
                )
            )
            continue
        candidate = (root / relative).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issues.append(
                _issue(
                    "error",
                    "asset-path-escape",
                    f"$.assets[{index}].path",
                    "자산 경로가 작업 디렉터리 밖으로 나갑니다.",
                )
            )
            continue
        if candidate.suffix.lower() not in _IMAGE_EXTENSIONS:
            issues.append(
                _issue(
                    "error",
                    "unsupported-image-format",
                    f"$.assets[{index}].path",
                    "PNG 또는 JPEG 이미지만 지원합니다.",
                )
            )
        if not candidate.is_file():
            issues.append(
                _issue(
                    "error",
                    "missing-asset-file",
                    f"$.assets[{index}].path",
                    f"자산 파일을 찾을 수 없습니다: {asset.path}",
                )
            )
        elif candidate.suffix.lower() in _IMAGE_EXTENSIONS and not _has_expected_image_signature(
            candidate
        ):
            issues.append(
                _issue(
                    "error",
                    "image-signature-mismatch",
                    f"$.assets[{index}].path",
                    "파일 내용이 확장자에 맞는 PNG 또는 JPEG가 아닙니다.",
                )
            )

    used_assets: set[str] = set()
    for question_index, question in enumerate(exam.questions):
        for choice_index, choice in enumerate(question.choices):
            if _CHOICE_MARK_RE.match(choice):
                issues.append(
                    _issue(
                        "error",
                        "embedded-choice-marker",
                        f"$.questions[{question_index}].choices[{choice_index}]",
                        "선택지 번호는 렌더러가 붙입니다. 선택지 본문에서 원문자 번호를 빼세요.",
                    )
                )
        for image_id in question.image_ids:
            used_assets.add(image_id)
            if image_id not in asset_map:
                issues.append(
                    _issue(
                        "error",
                        "missing-image-reference",
                        f"$.questions[{question_index}].image_ids",
                        f"정의되지 않은 이미지 ID: {image_id}",
                    )
                )
        estimated_lines = _estimate_question_lines(question)
        if question.keep_together and estimated_lines > exam.layout.max_lines_per_column:
            limit = exam.layout.max_lines_per_column
            issues.append(
                _issue(
                    "error",
                    "keep-together-overflow-risk",
                    f"$.questions[{question_index}]",
                    f"예상 {estimated_lines}줄로 한 단의 한도 {limit}줄을 넘습니다.",
                )
            )

    for unused in sorted(set(asset_ids) - used_assets):
        issues.append(
            _issue(
                "warning", "orphan-asset", "$.assets", f"어느 문항도 사용하지 않는 자산: {unused}"
            )
        )

    referenced_questions = {
        question_id for passage in exam.passages for question_id in passage.question_ids
    }
    for missing in sorted(referenced_questions - set(question_ids)):
        issues.append(_issue("error", "missing-question", "$.blocks", f"없는 문항 참조: {missing}"))

    return ValidationReport.from_issues(issues)


def load_and_validate(path: Path) -> tuple[ExamPaper | None, ValidationReport]:
    """Load one JSON file and return a model plus a stable validation report."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issue = _issue("error", "invalid-json", "$", f"JSON을 읽을 수 없습니다: {exc}")
        return None, ValidationReport.from_issues([issue])
    try:
        exam = ExamPaper.model_validate(payload)
    except ValidationError as exc:
        issues = [
            _issue(
                "error",
                "schema",
                "$"
                + "".join(
                    f"[{part}]" if isinstance(part, int) else f".{part}" for part in error["loc"]
                ),
                error["msg"],
            )
            for error in exc.errors(include_url=False)
        ]
        return None, ValidationReport.from_issues(issues)
    return exam, validate_exam(exam, root=path.parent)
