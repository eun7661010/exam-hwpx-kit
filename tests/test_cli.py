from __future__ import annotations

from pathlib import Path

import pytest

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


def test_help_is_bilingual(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        run(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "검증" in out
    assert "validate" in out


def test_subcommand_help_documents_every_option(capsys) -> None:
    for command in ("validate", "render", "audit", "template", "visual-check"):
        with pytest.raises(SystemExit):
            run([command, "--help"])
        out = capsys.readouterr().out
        assert " / " in out, command
