# exam-hwpx-kit

[![CI](https://github.com/eun7661010/exam-hwpx-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/eun7661010/exam-hwpx-kit/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/eun7661010/exam-hwpx-kit)](https://github.com/eun7661010/exam-hwpx-kit/releases)
[![Python](https://img.shields.io/badge/python-3.10--3.13-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

**구조화된 시험 JSON을 한국어 2단 HWPX 학습지로 만들고, 생성된 파일에
지문·문항·선택지·보기·이미지·단 설정이 그대로 남았는지 확인합니다.**

[English](README.md)

## 어떤 문제를 해결하나요?

시험 콘텐츠는 JSON이나 데이터베이스, AI가 작성한 초안에서 시작할 수 있습니다.
하지만 HWPX를 만드는 과정은 일회성 스크립트에 맡기는 경우가 많습니다. 이미지가
빠지거나 문항 번호가 겹치고, 개인 PC의 절대 경로가 들어가거나, 선택지와 문단이
조용히 누락되어도 파일을 직접 열기 전에는 알아차리기 어렵습니다.

`exam-hwpx-kit`는 이 과정의 앞뒤에 작고 검증 가능한 계약을 둡니다.

```text
시험 JSON + 상대 경로 자산
          │
          ▼
   스키마·내용 관계 검사
          │
          ▼
  python-hwpx 공개 저작 API
          │
          ▼
  2단 HWPX + 검증 영수증
          │
          ▼
 패키지·ID·텍스트·이미지·단 설정 감사
```

교사와 평가 콘텐츠 제작팀, 교육 서비스 개발자, AI 에이전트가 OWPML XML을
직접 작성하지 않고도 결정적인 JSON→HWPX 시험지 생성 과정을 구성할 수 있습니다.

## 무엇을 찾아내나요?

- 블록 ID, 문항 번호, 자산 ID가 중복된 경우
- 지문이 없거나 앞에 있는 문항을 참조한 경우
- 이미지가 없거나, 절대 경로이거나, 작업 폴더 밖으로 나가는 경우
- PNG·JPEG 파일의 실제 내용이 확장자와 맞지 않는 경우
- 정의하지 않은 이미지를 참조하거나 어느 문항도 쓰지 않는 자산이 있는 경우
- 선택지 본문에 원문자 번호가 이미 들어간 경우
- HWPX를 만들기 전에 XML에서 허용하지 않는 제어 문자를 발견한 경우
- 한 단에 들어갈 수 없는 문항에 `keep_together`를 지정한 경우
- 생성된 HWPX의 패키지 구조, 편집기 열림 안전, 공유 자원 ID가 깨진 경우
- 생성된 문서에서 지문·문항·선택지·배점·보기 텍스트가 빠지거나 중복되고, 순서가 바뀌거나 예상하지 않은 텍스트가 추가된 경우
- 원본 이미지가 빠지거나 다른 이미지로 바뀌고, 한 단·두 단 설정이 입력과 맞지 않는 경우

## 3분 빠른 시작

Windows, macOS, Linux의 Python 3.10~3.13을 지원합니다.

```bash
git clone https://github.com/eun7661010/exam-hwpx-kit.git
cd exam-hwpx-kit
python -m venv .venv
python -m pip install -e .

exam-hwpx validate examples/synthetic-exam.json
exam-hwpx render examples/synthetic-exam.json synthetic-exam.hwpx
exam-hwpx audit examples/synthetic-exam.json synthetic-exam.hwpx
```

다음과 같은 결과가 나옵니다.

```text
검증 통과: 오류 0개, 경고 0개
생성 완료: synthetic-exam.hwpx (문항 2개, 이미지 1개)
감사 통과
```

`render` 명령은 문서 옆에 `synthetic-exam.hwpx.receipt.json`도 만듭니다.
이 영수증에는 원본과 결과의 SHA-256 해시, 문항 수, 이미지 수, 입력 검증 결과,
출력 감사 결과가 들어갑니다. 개인 경로가 드러나지 않도록 파일명만 기록합니다.

저장소의 예제와 이미지는 모두 합성 자료입니다. 학생 정보, 실제 시험 지문,
기관 로고, 비공개 HWPX 템플릿을 포함하지 않습니다.

CLI를 실행하기 전에도 [합성 HWPX 결과](examples/synthetic-output.hwpx)와
[빈 합성 템플릿](examples/synthetic-template.hwpx)을 직접 확인할 수 있습니다.

## 입력 형식과 지원 범위

가장 작은 입력은 다음과 같습니다.

```json
{
  "schema_version": "exam-hwpx-kit/v1",
  "title": "합성 독해 연습지",
  "layout": { "columns": 2 },
  "assets": [],
  "blocks": [
    {
      "type": "question",
      "id": "q1",
      "number": 1,
      "stem": "합성 지문에서 알 수 있는 내용은?",
      "choices": ["선택지 A", "선택지 B"],
      "keep_together": true
    }
  ]
}
```

전체 계약에서는 다음 내용을 표현할 수 있습니다.

- A4 한 단 또는 두 단과 여백, 단 간격
- 여러 문항이 함께 쓰는 흐르는 지문
- 2~5개 선택지와 선택적 배점이 있는 문항
- `<보기>`와 같은 짧은 보조 상자
- 대체 설명과 표시 너비가 있는 상대 경로 PNG·JPEG 이미지
- 문항 분리 방지 의도와 보수적인 렌더 전 오버플로 위험 한도

필드의 자세한 내용은 [JSON Schema](src/exam_hwpx_kit/schemas/exam-paper.v1.schema.json)와
[스키마 안내](docs/schema.md)에서 확인할 수 있습니다.

## 명령어

| 명령 | 역할 | 종료 코드 |
|---|---|---:|
| `exam-hwpx validate INPUT` | 스키마·참조 관계·경로·자산·레이아웃 위험을 검사합니다. | 통과 `0`, 실패 `1` |
| `exam-hwpx render INPUT OUTPUT` | 기존 파일을 덮어쓰지 않으며, 검사 후 HWPX와 영수증을 만듭니다. | 성공 `0`, 차단 `1` |
| `exam-hwpx audit INPUT OUTPUT` | 기존 HWPX와 원본 JSON의 내용을 대조합니다. | 일치 `0`, 불일치 `1` |
| `exam-hwpx template OUTPUT` | 내용이 없는 합성 A4 HWPX 시작 파일을 만듭니다. | 성공 `0` |
| `exam-hwpx visual-check BASELINE CURRENT` | 외부 렌더러가 만든 PNG 페이지를 비교합니다. | 기준 이내 `0`, 회귀 `1` |

`validate`, `render`, `audit`, `visual-check`에 `--json`을 붙이면 기계가 읽을 수
있는 안정적인 JSON 결과를 출력합니다. `visual-check`를 쓰려면
`exam-hwpx-kit[visual]`을 설치하세요.

## 기존 공개 프로젝트와 어떻게 다른가요?

이 프로젝트는 시험 콘텐츠에 필요한 얇은 계층만 맡습니다. HWPX 패키지 생성과
문단·표·그림·단 설정·패키지 검사는 Apache-2.0으로 공개된
[`python-hwpx`](https://github.com/airmang/python-hwpx)에 맡깁니다.

[`python-hwpx-automation`](https://github.com/airmang/python-hwpx-automation)은
Markdown 문항을 기존 양식에 조판하고, 렌더러를 이용해 문항 분리를 측정하는 기능을
이미 제공합니다. `exam-hwpx-kit`는 그 기능을 다시 만들지 않습니다. 대신 버전이
있는 JSON 계약, 자산 경로 보호, 보기와 이미지가 포함된 문항, 입력 사전 검사,
합성 문서 생성, 원본과 결과를 대조하는 영수증을 제공합니다. 두 프로젝트는 서로
보완하는 관계입니다.

## 검증 수준을 구분합니다

이 프로젝트에서 `검증`은 다음과 같이 구분합니다.

1. **입력 검증**은 JSON 스키마, 내용 관계, 경로, 자산이 규칙을 통과했다는 뜻입니다.
2. **구조 검증**은 HWPX 패키지와 편집기 열림 안전, 공유 자원 ID, 단 설정,
   정규화한 전체 텍스트의 내용과 순서, 원본 이미지의 해시가 검사를 통과했다는 뜻입니다.
3. **시각 비교**는 신뢰할 수 있는 외부 렌더러가 만든 PNG를 `visual-check`로
   비교했다는 뜻입니다.
4. **한컴오피스에서 열림**은 사용자의 환경에서 직접 확인하지 않았다면 주장하지 않습니다.

`python-hwpx`는 형식에 맞는 구조 검사를 제공하지만, 구조 검사가 화면의 픽셀까지
보장하지는 않습니다. 자세한 절차는 [시각 회귀 검사](docs/visual-regression.md)를
참고하세요.

## 개인정보와 보안

CLI는 LLM을 호출하거나 문서를 업로드하지 않으며 네트워크 서비스도 사용하지
않습니다. 자산은 JSON 파일을 기준으로 한 상대 경로만 허용하며, 경로를 해석한
뒤에도 해당 폴더 안에 있어야 합니다. 영수증에는 절대 경로를 넣지 않고 파일명과
해시만 기록합니다.

이 도구는 입력 자료의 저작권이나 공개 가능 여부를 판정하지 않습니다. 학생 기록,
답안지, 인증 정보, 비공개 시험지, 권리가 불분명한 제3자 지문을 공개 저장소에 넣지
마세요. [보안 범위](docs/security-model.md)와 [보안 정책](SECURITY.md)도 확인하세요.

## 개발과 기여

```bash
python -m pip install -e ".[dev]"
python tools/generate_synthetic_assets.py
python tools/export_schema.py
ruff check .
ruff format --check .
mypy src
pytest --cov=exam_hwpx_kit --cov-report=term-missing
python -m build
twine check dist/*
```

CI는 Windows, macOS, Ubuntu의 Python 3.10과 3.13에서 테스트와 대표 예제를
실행합니다. 합성 fixture 규칙과 PR 절차는 [CONTRIBUTING.md](CONTRIBUTING.md)에
정리되어 있습니다.

## 하지 않는 일과 현재 한계

- 범용 HWPX 편집기, 렌더러, OCR, 문항 생성기는 제공하지 않습니다.
- 답안 보안, DRM, 전자서명, 시험 보안을 제공하지 않습니다.
- 정적 오버플로 검사는 보수적인 위험 신호입니다. 실제 쪽·단 넘침은 신뢰할 수 있는
  렌더러와 사람의 시각 검토로 확인해야 합니다.
- 보기 상자는 간단한 1×1 표로 만듭니다. 긴 지문은 표에 가두지 않고 본문으로 흘립니다.
- 0.1 버전은 PNG·JPEG 이미지와 일반 텍스트 지문·선택지를 지원합니다.
- 운영체제와 오피스 프로그램에 설치된 글꼴에 따라 줄바꿈이 달라질 수 있습니다.

## 라이선스와 출처

Apache License 2.0으로 공개합니다. 비공개 프로젝트의 코드·템플릿·지문·문항·자산은
포함하지 않습니다. 의존성과 합성 fixture의 출처는 [NOTICE](NOTICE)에 기록했습니다.
