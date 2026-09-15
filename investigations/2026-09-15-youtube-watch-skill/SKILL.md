---
name: youtube-watch
description: >-
  Analyze YouTube videos into frames, transcript, and Korean cut-table reports.
license: MIT
metadata:
  spec: youtube-watch/1.0
  output-contract: persona
  selftest: scripts/analyze_video.py --selftest
---

# youtube-watch Skill

유튜브 링크(또는 yt-dlp 지원 사이트, 로컬 영상)를 받아 프레임·자막·보고서로
분석한다. 이 스크립트는 프레임과 자막을 만들고, 에이전트가 프레임을 비전으로
읽어 보고서를 작성한다.

## When to Use

- 유튜브 링크를 "분석해줘"와 함께 받았을 때
- 영상 콘텐츠의 구조(컷 구성, 훅, 화면 텍스트)를 뽑아야 할 때
- Don't use for: 실시간 시청, 영상 편집/다운로드만 필요한 경우 (yt-dlp 직접 사용)

## Prerequisites

- yt-dlp ≥ 2026.01 (`yt-dlp --version`으로 확인)
- ffmpeg + ffprobe (`ffmpeg -version`)
- faster-whisper (pip; CPU small/int8 기준, 30분+ 영상은 수십 분 소요 경고)

설치 방법은 이 파일에 없다 — 설치 절차는 설치자 문서(설계 문서 §4) 소관이다.

## How to Run

```
terminal(command="python3 scripts/analyze_video.py <URL> --outdir <결과디렉토리>")
```

## Procedure

1. `analyze_video.py <URL>` 실행 — 산출물: frames/*.jpg, transcript.txt, index.json
   완료 기준: index.json 존재 + frames 1장 이상.
2. index.json의 frames를 순서대로 네이티브 비전 도구로 읽는다. 화면 텍스트·장면
   구성을 판독한다. 완료 기준: 모든 프레임 판독 누락 없음.
3. transcript.txt의 타임스탬프 자막을 프레임 경계에 조인해 컷별 표 작성
   (templates/cut-table.md 스키마). 완료 기준: 컷 수 = 프레임 수.
4. 페르소나 출력 계약(언어·후킹 멘트·분석·적용 제안)에 따라 보고서 작성.
   완료 기준: 보고서 4섹션 모두 존재.

## Pitfalls

- Shorts·연령제한 콘텐츠: yt-dlp 실패 가능. 1회 재시도 후 사용자 보고.
- 화면 녹화형 영상(코드/문서 촬영): 첫 2~3프레임으로 콘텐츠 유형 선감별 후
  --max-frames 늘려 밀도 샘플링.
- 비전 전달 시 540p 축소 권장 (1080p 원본에서 축소해도 화면 텍스트 판독 가능 — 실측).
- whisper 언어: 기본 ko. 영어 영상은 스크립트 내 language 파라미터 조정.

## Verification

검증 계약: `python3 scripts/analyze_video.py --selftest`
성공 판정: exit 0 + "PASS" 출력 (합성 클립 기반, 네트워크 불요).
의존성: Prerequisites 3항목 — selftest가 ffmpeg·whisper 로딩까지 통합 검증한다.

## Output Contract

보고서 형식(언어, 후킹 멘트 강조, 컷별 표, 분석·제안 섹션)은 페르소나 계약을
따른다. 스키마는 templates/cut-table.md 참조.
