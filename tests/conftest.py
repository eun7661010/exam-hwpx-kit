from __future__ import annotations

import json
from pathlib import Path

import pytest

from exam_hwpx_kit.models import ExamPaper


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def example_path(repo_root: Path) -> Path:
    return repo_root / "examples" / "synthetic-exam.json"


@pytest.fixture
def example_payload(example_path: Path) -> dict:
    return json.loads(example_path.read_text(encoding="utf-8"))


@pytest.fixture
def example_exam(example_payload: dict) -> ExamPaper:
    return ExamPaper.model_validate(example_payload)
