"""Renderer-neutral image comparison for externally rasterized exam pages."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class PageComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    page: str
    ok: bool
    changed_pixel_ratio: float
    reason: str = ""


class VisualReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool
    pages: tuple[PageComparison, ...]


def compare_page_directories(
    baseline_dir: Path,
    current_dir: Path,
    *,
    max_changed_pixel_ratio: float = 0.001,
    pixel_delta_threshold: int = 8,
) -> VisualReport:
    """Compare equally sized PNG pages created by any trusted HWPX renderer."""

    try:
        from PIL import Image, ImageChops
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError("visual-check에는 'exam-hwpx-kit[visual]' 설치가 필요합니다.") from exc

    baseline = {path.name: path for path in baseline_dir.glob("*.png")}
    current = {path.name: path for path in current_dir.glob("*.png")}
    pages: list[PageComparison] = []

    for name in sorted(set(baseline) | set(current)):
        if name not in baseline or name not in current:
            pages.append(
                PageComparison(
                    page=name, ok=False, changed_pixel_ratio=1.0, reason="페이지 집합이 다릅니다."
                )
            )
            continue
        with Image.open(baseline[name]) as before_image, Image.open(current[name]) as after_image:
            before = before_image.convert("RGB")
            after = after_image.convert("RGB")
            if before.size != after.size:
                pages.append(
                    PageComparison(
                        page=name,
                        ok=False,
                        changed_pixel_ratio=1.0,
                        reason="이미지 크기가 다릅니다.",
                    )
                )
                continue
            diff = ImageChops.difference(before, after).convert("L")
            changed = sum(
                count
                for value, count in enumerate(diff.histogram())
                if value > pixel_delta_threshold
            )
            ratio = changed / (before.width * before.height)
            pages.append(
                PageComparison(
                    page=name, ok=ratio <= max_changed_pixel_ratio, changed_pixel_ratio=ratio
                )
            )

    if not pages:
        pages.append(
            PageComparison(
                page="", ok=False, changed_pixel_ratio=1.0, reason="비교할 PNG 페이지가 없습니다."
            )
        )
    return VisualReport(ok=all(page.ok for page in pages), pages=tuple(pages))
