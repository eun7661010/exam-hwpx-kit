from __future__ import annotations

from pathlib import Path

from exam_hwpx_kit.cli import _ensure_utf8_stream, run


class NonUtf8Stream:
    encoding = "cp1252"

    def __init__(self) -> None:
        self.configured: tuple[str, str] | None = None

    def reconfigure(self, *, encoding: str, errors: str) -> None:
        self.configured = (encoding, errors)


def test_non_korean_console_is_reconfigured_to_utf8() -> None:
    stream = NonUtf8Stream()
    _ensure_utf8_stream(stream)
    assert stream.configured == ("utf-8", "backslashreplace")


def test_validate_human(example_path: Path, capsys) -> None:
    assert run(["validate", str(example_path)]) == 0
    assert "검증 통과" in capsys.readouterr().out


def test_validate_json(example_path: Path, capsys) -> None:
    assert run(["validate", str(example_path), "--json"]) == 0
    assert '"ok": true' in capsys.readouterr().out


def test_render_and_audit(example_path: Path, tmp_path: Path, capsys) -> None:
    output = tmp_path / "exam.hwpx"
    assert run(["render", str(example_path), str(output)]) == 0
    assert output.is_file()
    assert "생성 완료" in capsys.readouterr().out
    assert run(["audit", str(example_path), str(output)]) == 0
    assert "감사 통과" in capsys.readouterr().out


def test_template_command(tmp_path: Path) -> None:
    output = tmp_path / "template.hwpx"
    assert run(["template", str(output)]) == 0
    assert output.is_file()


def test_bad_input_returns_one(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text("{}", encoding="utf-8")
    assert run(["validate", str(source)]) == 1
