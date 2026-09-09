# 기여 안내

[English](CONTRIBUTING.md)

`exam-hwpx-kit`를 개선해 주셔서 감사합니다. 작은 수정, 새 검증 규칙, 여러
운영체제에서의 재현 보고, 문서, 접근성 개선 모두 환영합니다. 이슈와 PR은 한국어로
작성해도 됩니다.

## Pull Request를 열기 전에

1. 기존 이슈를 검색하고, 사용자에게 보이는 문제를 설명합니다.
2. 문제를 재현하는 합성 fixture를 추가하거나 갱신합니다.
3. HWPX 형식 자체의 작업은 `python-hwpx`에 두고, 이 저장소는 시험 계약, 도메인
   레이아웃, 원본과 결과의 무결성에 집중합니다.
4. 공개 계약이 바뀌면 JSON Schema와 문서를 함께 갱신합니다.
5. 아래 로컬 게이트를 전부 실행합니다.

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
git diff --exit-code
```

## fixture 안전 규칙

이 저장소를 위해 새로 만든 자료만 제출하세요. 다음은 제출하면 안 됩니다.

- 학생, 학부모, 교사, 직원, 고객 데이터
- 실제 시험, 지문, 문항, 답안지, 비공개 템플릿
- 기관 이름, 로고, 워터마크, 내부 호스트 이름, 서비스 ID
- 개인 절대 경로, 홈 디렉터리 이름, API 키, 토큰, 쿠키, `.env` 파일
- 재배포 허가가 분명하지 않은 이미지, 글꼴, 문서

모든 바이너리 fixture는 근처 `NOTICE.md`에 만든 방법을 적어 주세요. 결정적으로
재생성되는 스크립트를 권장합니다. 출처를 확인할 수 없는 fixture는 리뷰어가 제거하거나
거부할 수 있습니다.

## 계약 변경

저장소의 JSON Schema는 `ExamPaper` 모델에서 생성됩니다. 모델을 바꾸는 PR은
`python tools/export_schema.py`를 실행하고 스키마 diff를 포함해야 합니다. 의미가
바뀌거나 필수 필드가 추가되면 새 `schema_version`과 이전(migration) 메모가
필요합니다.

고정된 이슈 코드와 CLI 종료 코드는 공개 API입니다. 호환 계획을 문서화한 경우에만
이름을 바꿀 수 있습니다.

## HWPX 변경

이 프로젝트에서는 OWPML XML을 직접 작성하지 않습니다. 공개 `python-hwpx` API를
쓰세요. 공개 관찰 API가 없을 때 감사를 위해 생성된 XML을 읽는 것은 괜찮지만, 코드가
XML을 바꿔서는 안 됩니다.

시각적 변경에는 다음이 필요합니다.

- 구조 테스트
- 합성 HWPX 예제
- PNG 기준선이 있다면 렌더러, 운영체제, 글꼴, 내보내기 설정
- 한컴오피스에서 확인하지 않았다면 그 사실을 분명히 적기

## 커밋과 리뷰 범위

PR은 한 가지 주제에 집중해 주세요. 이전에 무엇이 실패했고, 새 불변 조건이 무엇이며,
어떤 테스트가 그것을 증명하는지 설명해 주세요. 기여자는 제출로써 Apache-2.0 아래
작업을 인증하며, 별도의 기여자 라이선스 동의서는 필요하지 않습니다.
