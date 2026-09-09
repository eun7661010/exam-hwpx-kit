# 문제 해결

[English](troubleshooting.md)

## `absolute-asset-path` 또는 `asset-path-escape`

이미지를 JSON 파일이 있는 폴더 아래로 옮기고 `assets/chart.png`처럼 상대 경로를
쓰세요. 특정 PC에만 있는 경로로 이 규칙을 우회하지 마세요.

## `embedded-choice-marker`

선택지에는 본문만 저장하세요. `①`~`⑤`는 렌더러가 붙입니다. JSON에서 표시를 빼면
번호가 두 번 붙는 일을 막고, 원본을 렌더러에 중립적으로 유지할 수 있습니다.

## `keep-together-overflow-risk`

문항을 줄이거나 나누고, 큰 이미지나 보기 상자를 줄이거나, 장단점을 검토한 뒤
`keep_together`를 `false`로 두세요. `max_lines_per_column`을 올리는 것은 정적
위험 기준만 바꿀 뿐, 쪽에 공간을 더 만들지는 않습니다.

## `invalid-json`

파일이 올바른 JSON이 아니거나 읽을 수 없습니다. 메모장과 Windows PowerShell 5의
`Out-File`이 기본으로 붙이는 UTF-8 BOM은 허용합니다. UTF-16 파일, 끝에 남은 쉼표,
주석은 여전히 실패하니 UTF-8로 저장하고 문법을 먼저 고치세요.

## `schema`

필드가 빠졌거나, 형식이 다르거나, 알 수 없는 필드가 있습니다. 메시지의 경로(예:
`$.blocks[1].choices[0]`)가 정확한 위치를 가리킵니다. 빈 문자열은 선택지를 포함해
어디서도 허용하지 않습니다.

## `duplicate-block-id`, `duplicate-question-number`, `duplicate-asset-id`

블록 ID, 문항 번호, 자산 ID는 한 문서 안에서 중복될 수 없습니다. 이름이나 번호를
바꾸세요. 감사는 고정된 ID에 의존합니다.

## `question-order` (경고)

문항 번호가 오름차순이 아닙니다. 생성은 계속되지만, 의도한 순서가 아니라면 블록을
다시 정렬하세요.

## `duplicate-passage-reference`, `missing-passage-question`, `passage-order`, `missing-question`

지문이 같은 문항을 두 번 적었거나, 없는 문항 ID를 참조하거나, 참조하는 문항보다 뒤에
있습니다. 지문을 문항보다 앞에 두고 각 문항을 한 번만 적으세요.

## `missing-image-reference`

문항이 `assets`에 없는 이미지 ID를 참조합니다. 자산을 추가하거나 ID를 고치세요.

## `unsupported-image-format`, `missing-asset-file`, `image-signature-mismatch`

`.png`, `.jpg`, `.jpeg`만 허용하고, 파일은 JSON 폴더 아래에 실제로 있어야 하며, 파일
내용이 확장자와 맞아야 합니다. 확장자만 바꾼 WebP나 SVG는 서명 검사에서 실패하니
PNG나 JPEG로 다시 내보내세요.

## `orphan-asset` (경고)

선언은 했지만 어느 문항도 쓰지 않는 자산이라 문서에 들어가지 않습니다. 지우거나
문항에서 참조하세요.

## `unsafe-control-character`

XML이 허용하지 않는 제어 문자(예: U+0000, U+001B)가 텍스트에 있습니다. 대개
복사·붙여넣기로 들어오니 원본에서 지우세요.

## 구조 감사는 통과했는데 쪽 모양이 이상합니다

패키지·내용 무결성은 시각 렌더링이 아닙니다. 신뢰할 수 있는 오피스 프로그램으로
쪽을 내보내고, 필요한 글꼴이 있는지 확인한 뒤
[`visual-regression.ko.md`](visual-regression.ko.md)의 절차를 따르세요.

## 한국어 텍스트는 있는데 줄바꿈이 다릅니다

글꼴 대체와 오피스 프로그램의 조판 엔진이 줄바꿈에 영향을 줍니다. 시각적 안정성이
중요하다면 렌더러, 운영체제, 글꼴 파일, 내보내기 설정을 고정하세요.

## `visual-check`가 추가 패키지가 없다고 합니다

선택 의존성을 설치하세요.

```bash
python -m pip install "exam-hwpx-kit[visual]"
```

## Windows 콘솔에서 한국어가 깨져 보입니다

CLI는 콘솔이 한국어를 표현할 수 없는 코드 페이지를 쓰면 출력을 UTF-8로 바꿔
줍니다. 그래도 깨진다면 PowerShell이나 명령 프롬프트에서 `chcp 65001`을 실행하거나,
환경 변수 `PYTHONUTF8=1`을 설정한 뒤 다시 실행하세요.
