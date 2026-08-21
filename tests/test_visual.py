from __future__ import annotations

from pathlib import Path

from PIL import Image

from exam_hwpx_kit.visual import compare_page_directories


def save(path: Path, color: str, size: tuple[int, int] = (20, 20)) -> None:
    Image.new("RGB", size, color).save(path)


def test_identical_pages_pass(tmp_path: Path) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    before.mkdir()
    after.mkdir()
    save(before / "page-1.png", "white")
    save(after / "page-1.png", "white")
    report = compare_page_directories(before, after)
    assert report.ok
    assert report.pages[0].changed_pixel_ratio == 0


def test_changed_pages_fail(tmp_path: Path) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    before.mkdir()
    after.mkdir()
    save(before / "page-1.png", "white")
    save(after / "page-1.png", "black")
    assert compare_page_directories(before, after).ok is False


def test_page_set_mismatch_fails(tmp_path: Path) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    before.mkdir()
    after.mkdir()
    save(before / "page-1.png", "white")
    assert compare_page_directories(before, after).ok is False


def test_size_mismatch_fails(tmp_path: Path) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    before.mkdir()
    after.mkdir()
    save(before / "page-1.png", "white", (20, 20))
    save(after / "page-1.png", "white", (21, 20))
    assert compare_page_directories(before, after).ok is False
