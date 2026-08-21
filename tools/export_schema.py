"""Export the public Pydantic contract as a checked-in JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path

from exam_hwpx_kit.models import ExamPaper


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "src" / "exam_hwpx_kit" / "schemas" / "exam-paper.v1.schema.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    schema = ExamPaper.model_json_schema()
    schema["$id"] = (
        "https://github.com/eun7661010/exam-hwpx-kit/blob/v0.1.0/src/exam_hwpx_kit/schemas/exam-paper.v1.schema.json"
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    target.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"generated {target.relative_to(root)}")


if __name__ == "__main__":
    main()
