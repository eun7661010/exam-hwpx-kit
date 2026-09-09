"""Command-line interface for exam-hwpx-kit."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from . import __version__
from .audit import audit_hwpx
from .models import ExamPaper
from .render import RenderError, create_template, render_exam
from .validation import ValidationReport, load_and_validate
from .visual import compare_page_directories


def _ensure_utf8_stream(stream: Any) -> None:
    """Use UTF-8 when a Windows shell exposes a non-Korean code page."""

    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        "검".encode(encoding)
    except (LookupError, UnicodeEncodeError):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def _print_report(report: ValidationReport, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
        return
    status = "통과" if report.ok else "실패"
    print(f"검증 {status}: 오류 {report.errors}개, 경고 {report.warnings}개")
    for issue in report.issues:
        print(f"[{issue.severity}] {issue.code} {issue.path}: {issue.message}")


def _load_for_command(path: Path, *, as_json: bool = False) -> tuple[ExamPaper | None, int]:
    exam, report = load_and_validate(path)
    if not report.ok:
        _print_report(report, as_json=as_json)
        return None, 1
    return exam, 0


_INPUT_HELP = "시험 JSON 파일 / exam JSON file"
_OUTPUT_HELP = "만들 HWPX 파일 경로 / HWPX path to create"
_JSON_HELP = "기계가 읽을 수 있는 JSON을 출력합니다 / print machine-readable JSON"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="exam-hwpx",
        description=(
            "시험 JSON을 검증하고 2단 HWPX를 만든 뒤 결과를 감사합니다. / "
            "Validate exam JSON, generate two-column HWPX, and audit the result."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser(
        "validate", help="JSON과 참조 자산을 검증합니다 / validate JSON and referenced assets"
    )
    validate_parser.add_argument("input", type=Path, help=_INPUT_HELP)
    validate_parser.add_argument("--json", action="store_true", help=_JSON_HELP)

    render_parser = subparsers.add_parser(
        "render", help="검증된 JSON으로 HWPX를 만듭니다 / render validated JSON to HWPX"
    )
    render_parser.add_argument("input", type=Path, help=_INPUT_HELP)
    render_parser.add_argument("output", type=Path, help=_OUTPUT_HELP)
    render_parser.add_argument(
        "--receipt", type=Path, help="영수증을 이 경로에 씁니다 / write receipt to this path"
    )
    render_parser.add_argument(
        "--json", action="store_true", help="영수증을 JSON으로 출력합니다 / print receipt as JSON"
    )

    audit_parser = subparsers.add_parser(
        "audit", help="HWPX를 원본 JSON과 대조합니다 / compare an HWPX with its source JSON"
    )
    audit_parser.add_argument("input", type=Path, help=_INPUT_HELP)
    audit_parser.add_argument("hwpx", type=Path, help="감사할 HWPX 파일 / HWPX file to audit")
    audit_parser.add_argument("--json", action="store_true", help=_JSON_HELP)

    template_parser = subparsers.add_parser(
        "template", help="내용이 없는 합성 HWPX를 만듭니다 / create a synthetic blank HWPX"
    )
    template_parser.add_argument("output", type=Path, help=_OUTPUT_HELP)
    template_parser.add_argument(
        "--columns",
        type=int,
        choices=(1, 2),
        default=2,
        help="단 수, 기본 2 / number of columns, default 2",
    )

    visual_parser = subparsers.add_parser(
        "visual-check",
        help="외부 렌더러가 만든 PNG 쪽을 비교합니다 / compare externally rendered PNG pages",
    )
    visual_parser.add_argument(
        "baseline", type=Path, help="기준 PNG 쪽 폴더 / directory of baseline PNG pages"
    )
    visual_parser.add_argument(
        "current", type=Path, help="비교할 PNG 쪽 폴더 / directory of current PNG pages"
    )
    visual_parser.add_argument(
        "--max-changed-pixel-ratio",
        type=float,
        default=0.001,
        help="쪽당 허용하는 바뀐 픽셀 비율, 기본 0.001 / allowed changed-pixel ratio per page",
    )
    visual_parser.add_argument(
        "--pixel-delta-threshold",
        type=int,
        default=8,
        help="바뀐 픽셀로 세는 회색조 차이, 기본 8 / grayscale delta that counts as changed",
    )
    visual_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        _, report = load_and_validate(args.input)
        _print_report(report, as_json=args.json)
        return 0 if report.ok else 1

    if args.command == "render":
        exam, code = _load_for_command(args.input, as_json=args.json)
        if exam is None:
            return code
        try:
            receipt = render_exam(
                exam,
                source_path=args.input,
                output_path=args.output,
                receipt_path=args.receipt,
            )
        except RenderError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(receipt.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            summary = f"문항 {receipt.questions}개, 이미지 {receipt.images}개"
            print(f"생성 완료: {args.output.name} ({summary})")
        return 0

    if args.command == "audit":
        exam, code = _load_for_command(args.input, as_json=args.json)
        if exam is None:
            return code
        audit_report = audit_hwpx(exam, args.hwpx, source_root=args.input.parent)
        if args.json:
            print(json.dumps(audit_report.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            print("감사 통과" if audit_report.ok else "감사 실패")
            for check in audit_report.checks:
                print(f"[{'ok' if check.ok else 'fail'}] {check.name}: {check.detail}")
        return 0 if audit_report.ok else 1

    if args.command == "template":
        try:
            create_template(args.output, columns=args.columns)
        except RenderError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"합성 템플릿 생성 완료: {args.output.name}")
        return 0

    if args.command == "visual-check":
        try:
            visual_report = compare_page_directories(
                args.baseline,
                args.current,
                max_changed_pixel_ratio=args.max_changed_pixel_ratio,
                pixel_delta_threshold=args.pixel_delta_threshold,
            )
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(visual_report.model_dump(mode="json"), ensure_ascii=False, indent=2))
        else:
            print("시각 비교 통과" if visual_report.ok else "시각 비교 실패")
            for page in visual_report.pages:
                print(f"{page.page}: changed={page.changed_pixel_ratio:.6f} {page.reason}")
        return 0 if visual_report.ok else 1
    return 2


def main() -> None:
    _ensure_utf8_stream(sys.stdout)
    _ensure_utf8_stream(sys.stderr)
    raise SystemExit(run())


if __name__ == "__main__":
    main()
