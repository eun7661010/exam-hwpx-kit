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
