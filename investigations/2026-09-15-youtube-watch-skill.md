# youtube-watch 스킬 설계 문서 (v1.0)

- 일자: 2026-09-15
- 작성: agentarch (에이전틱 코딩 설계 자문)
- 목적: 승우님이 만든 **유튜브 영상 분석 스킬**을 4개 하네스(Claude Code, Codex CLI, OpenCode, Hermes)에 이식하기 위한 설계 표준
- 이력: v0.1~v0.2 "범용 에이전트 스킬 표준안"을 단일 목적(유튜브 분석)으로 축소 개편. 범용 표준 문서는 폐기.
- 범위: **자작 스킬 이식 전용** — 서드파티 스킬 도입(남의 스킬이 시키는 셸 명령을 내 에이전트가 실행하는 문제)은 범위 밖.

---

## 0. 설계 목표

유튜브(및 yt-dlp가 지원하는 영상 사이트) 링크를 받아 프레임+자막 기반으로 분석
보고서를 내는 스킬 하나. 이것을 하네스마다 다시 쓰지 않고 이식하는 것이 목표다.

핵심 결정 3가지:

1. **스킬 코어는 유튜브 분석 지식만** — 절차(다운로드→프레임→자막→보고서), 요구
   도구, 검증 계약, 출력 계약. 하네스별 경로·설치 지식은 담지 않는다.
2. **설치는 스킬 밖의 설치자 절차 1개(§4)** — v0.1에서 "스킬 본문에 자가설치
   섹션"을 두었다가 폐기했다. 스킬 로딩 트리거는 description 매칭이고 인덱스에
   오르려면 복사가 먼저 끝나야 하므로, 본문의 설치 절차는 부트스트랩 모순이다
   (닭과 달걀). 설치 절차는 이 문서 §4 하나에만 둔다.
3. **기술 절차와 출력 계약의 분리(§3)** — "how to analyze"는 스킬 본문, "how to
   report"(한국어, 후킹 멘트 강조, 컷별 표)는 페르소나 레이어. 근거는 claudewatch
   릴스의 실측 프롬프트(§3 인용).

검증된 기반: 본 서버에서 파이프라인(yt-dlp 2026.08.19 → ffmpeg 장면전환 프레임 →
faster-whisper 자막 → index.json)을 실제 릴스(28.5초)로 돌려 프레임 7장 + 타임스탬프
자막 추출에 성공했다. 설계는 추상 스펙이 아니라 실측을 기반으로 한다.

---

## 1. 스킬이 하는 일 (기능 정의)

**입력**: 유튜브 URL (확장: yt-dlp 지원 사이트, 로컬 영상 파일)
**출력**: 마크다운 분석 보고서 (§3 출력 계약 형식)

처리 파이프라인:
1. yt-dlp 다운로드 (mp4)
2. ffmpeg 장면 전환 감지 기반 대표 프레임 추출 (길이 기반 자동 예산, 상한 24장)
3. faster-whisper 자막 추출 (타임스탬프 포함)
4. index.json 생성 (프레임·자막·메타의 시간축 정렬 데이터)
5. 에이전트가 프레임을 비전으로 읽고 자막과 조인해 보고서 작성

1~4는 scripts/ 실행기가, 5는 하네스 에이전트가 담당한다 — "도구가 프레임을
만들고, 에이전트가 읽는다"의 역할 분담.

---

## 2. 스킬 코어 (SKILL.md 표준)

스킬이 져야 할 책임은 자기 검증 계약이지 남의 파일시스템 지식이 아니다.
코어에는 유튜브 분석 지식만 둔다.

### 2.1 프론트매터

```yaml
---
name: youtube-watch
description: >                 # 트리거 조건이 앞 57자 안에 자족
  Analyze YouTube videos into frames, transcript, and Korean cut-table reports.
license: MIT
metadata:
  spec: youtube-watch/1.0
  output-contract: persona     # §3 사용 표시
  selftest: scripts/analyze_video.py --selftest
---
```

`name`+`description`만 전 하네스 공통 필수 (4종 하네스 공식 문서/검증기 확인).
미인식 프론트매터 필드는 하네스가 무시하므로 무해 (OpenCode 공식 문서 명시).

**description 57자 규칙**: 근거는 Hermes 실측값(스킬 인덱스가 57자+생략 부호로
절단). 타 하네스 절단 길이는 미측정 — 보수적 상한으로 채택. 트리거 인터페이스가
description 하나뿐(§5.2)이므로 이 제약이 스킬에서 가장 비싼 제약이다.

### 2.2 본문 섹션

```
# youtube-watch Skill
## When to Use        — 유튜브 링크 분석 요청. 역트리거: 실시간 시청, 편집 작업
## Prerequisites      — yt-dlp(≥2026.01), ffmpeg, faster-whisper (버전 명시만.
                        설치 방법은 쓰지 않는다 — 설치자 §4 소관)
## How to Run         — python3 scripts/analyze_video.py <URL>
## Procedure          — 파이프라인 단계별 완료 기준
## Pitfalls           — §1.1 함정 목록
## Verification       — 검증 계약 (§2.4)
## Output Contract    — "보고서 형식은 페르소나 계약(§3)을 따른다" 한 줄
```

- 각 절차 단계는 검증 가능한 완료 기준으로 끝난다.
- 하네스 고유 도구명을 직접 쓰지 않는다: "프레임을 네이티브 비전 도구로 읽는다"
  식으로 기술하고 구체 도구는 §5.3 매핑이 흡수한다.
- 머신 로컬 절대경로 금지.

### 2.3 폴더 구조 (자기완결)

```
youtube-watch/
├── SKILL.md
├── scripts/
│   └── analyze_video.py    # 파이프라인 실행기 + selftest
├── references/             # 하네스 어댑터 상세, 트러블슈팅
└── templates/
    └── cut-table.md        # 컷별 4칸 표 스키마 (준수 조건)
```

SKILL.md와 scripts/는 반드시 같은 폴더로 복사 가능해야 한다 (claude-video 사례:
scripts 분리 배포 시 비-Claude 호스트에서 dead on arrival).

### 2.4 검증 계약 (self-test contract)

스킬이 선언하고 설치자(§4)가 실행한다:

1. **selftest 명령**: `python3 scripts/analyze_video.py --selftest`
   - ffmpeg로 합성 3초 클립 생성 (네트워크 불요) → 파이프라인 전체 실행 →
     프레임 1장 이상 + transcript 파일 존재 확인 → exit 0
2. **성공 판정**: exit code 0 + 산출물 존재 (기계 판독 가능)
3. **의존성 선언**: Prerequisites와 일치하는 도구·버전

### 2.5 파이프라인 설계 파라미터 (실측·생태계 근거)

- **프레임 예산**: 길이 기반 자동 스케일 + 하드캡 24장. 60분 영상을 1fps로 뽑으면
  3,600장 — 컨텍스트 폭발. 업계 표준도 길이 기반+하드캡(claude-video: 100장/2fps).
- **장면 전환 감지 우선, 균등 샘플 폴백**: 전환 프레임이 절반에 못 미치면 균등
  간격으로 보충 (analyze_video.py 구현 검증 완료).
- **자막은 타임스탬프 필수**: `[0000.0s]` 형식으로 저장 — §3의 컷별 표가 프레임과
  자막을 시간축 조인하려면 필수. 출력 형식 명시가 곧 데이터 스키마 명시다.
- **Whisper 모델**: faster-whisper small/int8 (CPU 실측: 단편 영상 양호, 30분+
  경고 필요). Groq/OpenAI API 전사가 업계 트렌드지만 자작·무료 목표상 로컬 유지.

### 2.6 함정 목록 (Pitfalls)

- 유튜브 Shorts·연령제한 콘텐츠: yt-dlp 실패 가능. 1회 재시도 후 사용자 보고.
- 프레임은 1080p 스케일로 추출하되 비전 전달 시 540p 축소 권장 (비전 토큰 절약,
  본 서버 실측: 1080p 원본에서 540p로도 화면 텍스트 판독 가능).
- 화면 녹화형(코드/문서 촬영) 영상은 밀도 샘플링 필요 — 첫 2~3프레임으로
  콘텐츠 유형 선감별 후 샘플링 전략 결정.
- 긴 영상(10분+)은 selftest와 달리 실데이터 시험에 시간이 걸린다 — 설치 검증은
  반드시 합성 클립으로.

---

## 3. 출력 계약 (페르소나 레이어)

근거 — claudewatch 릴스 실측 프롬프트:

> "스킬이 영상 분석 결과를 낼 때는 항상 한국어로, 아래 형식을 따르게 SOUL.md에
> 명시해줘. - 후킹 멘트만 따로 강조해서 제일 위에 - 컷별 표: 타임스탬프/화면에
> 보이는 것/화면 텍스트/실제 대사 - '왜 이 구조가 먹히는지' 분석 - '내 콘텐츠에
> 적용할 점' 제안"

보고서 형식(언어·구조·강조)은 스킬이 아니라 각 하네스의 페르소나 파일에 둔다:

| 하네스 | 페르소나 파일 |
|---|---|
| Claude Code | CLAUDE.md (전역: ~/.claude/CLAUDE.md) |
| Codex CLI | AGENTS.md (~/.codex/AGENTS.md) |
| OpenCode | AGENTS.md / opencode.json rules |
| Hermes | SOUL.md (프로필별) |

기록할 내용 (릴스 실측 그대로):
1. 보고서는 항상 한국어
2. 후킹 멘트를 최상단에 별도 강조
3. 컷별 표: 타임스탬프 / 화면에 보이는 것 / 화면 텍스트 / 실제 대사
   (스키마: templates/cut-table.md — 프레임+자막의 시간축 조인 결과물)
4. "왜 이 구조가 먹히는지" 분석 섹션
5. "내 콘텐츠에 적용할 점" 제안 섹션

분할 이유: 스킬이 늘어도 보고서 형식은 하나로 유지된다. 새 분석 스킬을 추가해도
페르소나 계약은 재사용된다.

---

## 4. 설치자 (Installer) — 이 문서에만 존재

모든 자작 스킬에 공통 적용. 스킬 본문에는 없다.

1. **하네스 감지**: `~/.hermes/`→Hermes, `~/.claude/`→Claude Code,
   `~/.codex/`→Codex CLI, `~/.config/opencode/`→OpenCode. 복수 감지 시 사용자에게 문의.
2. **경로 결정**: §5.1 표 조회. 실측 열이 "미실측"이면 복사 전 실제 디렉토리 확인.
3. **복사**: youtube-watch/ 폴더 전체. 폴더명=frontmatter name.
   (Hermes: `hermes skills install <path>` — 보안 스캔 경유)
4. **의존성 설치 + 버전 보고**: yt-dlp/ffmpeg/faster-whisper 설치 후 `--version`
   출력을 그대로 보고 ("설치했다" ✗, 출력 증명 ○).
5. **검증 게이트**: `metadata.selftest` 실행 → §2.4 판정 기준과 대조.
6. **완료 보고**: 설치 경로 + 도구 버전 출력 + selftest 결과 3종.
7. **실패 시**: 1회 재시도 → 재실패 시 사용자 블록 보고.

근거(신뢰 모델): 릴스 실측 프롬프트의 "설치 끝나면 실제로 뭐가 깔렸는지 (yt-dlp,
ffmpeg, 음성인식 도구 버전) 확인해서 결과 알려줘" — 에이전트의 완료 주장을 산출물로
담보한다. 자작 스킬이므로 서드파티 신뢰 검증 단계는 불요 (작성자=본인).

---

## 5. 하네스 어댑터

### 5.1 설치 경로 (실측/출처 열 필수)

| 하네스 | 전역 | 프로젝트 | 출처 신뢰도 |
|---|---|---|---|
| Claude Code | `~/.claude/skills/youtube-watch/` | `.claude/skills/` | 공식 문서 (미실측) |
| Codex CLI | `~/.codex/skills/youtube-watch/` | `.codex/skills/` | **서드파티 가이드 (미실측)** — 설치 전 실측 필수 |
| OpenCode | `~/.config/opencode/skills/youtube-watch/` | `.opencode/skills/` | 공식 문서 (2026-09 확인) |
| OpenCode (호환) | `~/.agents/skills/`도 읽음 | `.agents/skills/`, `.claude/skills/`도 읽음 | 공식 문서 |
| Hermes | `~/.hermes/skills/<category>/youtube-watch/` | `.hermes/skills/`, `.agents/skills/` | 공식 문서 + **본 서버 실측** |

- 경로가 틀린 칸이 있으면 설치 루프 전체가 깨지므로 출처 신뢰도를 반드시 확인.
- `.agents/skills/`는 OpenCode+Hermes 공용 경로 (양쪽 공식 문서 확인) — 단일 복사로
  2종 동시 커버.
- Codex 칸이 유일한 서드파티 출처 — 최대 리스크. 설치 시 실측으로 방어.

### 5.2 트리거

| 하네스 | 트리거 |
|---|---|
| Claude Code | description 매칭 (자율) 또는 /youtube-watch |
| Codex CLI | description 매칭 (자율) |
| OpenCode | description 매칭 + permission 제어 가능 |
| Hermes | description 매칭 (자율) |

description이 사실상 유일한 트리거 인터페이스 → §2.1의 57자 규칙이 중요.

### 5.3 도구 능력 매핑

| 능력 | Claude Code | Codex CLI | OpenCode | Hermes |
|---|---|---|---|---|
| 이미지 읽기 | Read (멀티모달) | 미확인 | 모델 의존 | vision_analyze (네이티브) |
| 셸 실행 | Bash | 셸 네이티브 | 셸 | terminal |

비전 단계 분기: "네이티브 비전 도구가 있으면 그것으로, 없으면 프레임을 컨텍스트에
첨부 가능한 경로로 전달". Codex 비전은 미확인 — 실측 전까지 Codex 지원은 부분
지원으로 표기.

---

## 6. 구현 현황 (v1.1 — 전 항목 충족, 2026-09-15 실측)

**스킬 패키지 (youtube-watch/)**:
- SKILL.md — 코어 본문 (프론트매터에 selftest 포인터 포함)
- scripts/analyze_video.py — 파이프라인 + --selftest
- templates/cut-table.md — 컷별 4칸 표 스키마 (준수 조건으로 동봉 완료)

**실측 검증 결과**:
1. selftest: `--selftest` → ffmpeg 합성 3초 클립 → 파이프라인 전체 →
   **PASS (exit 0)**, 프레임 3장 + transcript + index.json 생성 확인. 네트워크 불요.
2. 유튜브 종단 시험: 실링크(youtube.com/watch?v=jNQXAC9IVRw, 19초) →
   yt-dlp 다운로드 → 프레임 6장 + 한국어 타임스탬프 자막([0000.1s] 형식) 추출 성공.
3. 비전 조인 검증: 프레임 판독(동물원 청년+코끼리)과 자막("엘리핀")이
   시간축에서 정확히 일치 — 컷별 표의 데이터 기반 확인.
4. 페이스북 릴스 획득 절차(og 메타 → lookaside crawler mp4)도 기존 실측 유지 —
   유튜브 외 소스 확장 근거.

youtube-watch는 본 설계 문서의 첫 준수 사례이자 실행 가능성이 실증됐다.

---

## 7. 미해결 과제

1. Codex 설치 경로 실측 (§5.1 — 유일한 서드파티 출처 칸)
2. 타 하네스 description 절단 길이 실측 (§2.1 — 57자가 보수적 상한인지 확인)
3. Codex 비전 능력 실측 (§5.3)
4. 준수 검증 스크립트 (frontmatter + 필수 섹션 + selftest 존재 체크)
