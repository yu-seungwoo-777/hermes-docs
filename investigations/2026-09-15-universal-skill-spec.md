# 범용 에이전트 스킬 표준안 (Universal Agent Skill Spec, 초안 v0.1)

- 일자: 2026-09-15
- 작성: agentarch (에이전틱 코딩 설계 자문)
- 목적: 한 번 작성한 SKILL.md 스킬이 여러 코딩 에이전트(Claude Code, Codex CLI, OpenCode, Hermes)에서 **에이전트가 스스로 읽고 자가 설치·실행**하도록 하는 표준안
- 상태: 초안 (승우님 검토 전)

---

## 0. 설계 목표와 배경

릴스(claudewatch) 사례와 외부 생태계 조사(bradautomates/claude-video 등)에서 확인된
문제: 같은 스킬이 하네스마다 경로·매니페스트·트리거 방식이 달라 재작성이 반복된다.

이 표준안의 목표는 재작성이 아니라 **이식**이다. 핵심 결정 3가지:

1. **코어는 작게, 어댑터는 표로** — 하네스 중립 본문 1개 + 하네스별 차이만 어댑터
   테이블(§5)로 흡수. 코어가 커질수록 하네스 진화 속도를 못 따라간다.
2. **자가설치 프로토콜 명문화(§4)** — 설치 주체를 사람이 아니라 에이전트로. 스킬이
   자신의 설치 절차를 셸 명령으로 기술하고, 에이전트는 그것을 읽고 실행·검증한다.
3. **기술 절차와 출력 계약의 분리(§3)** — "how to watch"는 스킬 본문, "how to
   report"(언어·형식·강조)는 페르소나 레이어. 이 분리가 없으면 스킬마다 보고서
   형식이 흩어진다.

선례: bradautomates/claude-video(★17.2k)는 skills/watch/ 자기완결형 폴더 +
.claude-plugin/.codex-plugin/.agents 3중 매니페스트로 같은 문제를 부분적으로 풀었다.
본 표준안은 이를 "에이전트 자가설치"까지 일반화한다.

---

## 1. 용어

- **하네스(harness)**: 에이전트 실행기. Claude Code, Codex CLI, OpenCode, Hermes.
- **코어(core)**: 하네스 중립적인 SKILL.md 본문. 모든 하네스가 동일하게 읽는 부분.
- **어댑터(adapter)**: 하네스별 차이(설치 경로, 트리거, 도구 대응)를 흡수하는 표/절차.
- **자가설치(self-install)**: 에이전트가 스펙의 설치 절차를 읽고 본인 하네스에
  스스로 이식하는 행위.

---

## 2. 코어 계약 (SKILL.md 최소 표준)

### 2.1 프론트매터

```yaml
---
name: video-watch              # 소문자+하이픈, 1-64자, 디렉토리명과 일치
description: >                 # 1문장, 마침표 종결. 트리거 조건을 앞 57자 안에
  Analyze any video link or file into frames, transcript, and cut table.
license: MIT
compatibility: universal       # 이 표준안 준수 표시
metadata:
  spec: uass/0.1               # 표준안 버전
  output-contract: persona     # §3 출력 계약 사용 표시
---
```

모든 하네스가 인정하는 공통 필수는 `name`, `description` 두 개뿐이다 (검증:

- Claude Code: name, description
- Codex CLI: name, description
- OpenCode: name, description (나머지 필드는 unknown 시 무시 — 공식 문서 확인)
- Hermes: name, description (validator는 version/author 등도 권장)

→ `name`/`description`만 필수로, 나머지는 선택. 미인식 필드는 하네스가 무시하므로
무해하다(OpenCode 공식 문서: "Unknown frontmatter fields are ignored").

**description 규칙**: 60자 내외 1문장, 마침표 종결, 마케팅 단어 금지. 시스템 프롬프트의
스킬 인덱스는 57자+생략 부호로 잘리므로 트리거 조건이 앞 57자 안에 자족해야 한다
(Hermes hardline 기준 — 가장 엄격한 쪽을 표준으로 채택).

### 2.2 본문 표준 섹션

```
# <스킬명> Skill
## When to Use        — 트리거 + 역트리거(Don't use for)
## Prerequisites      — 필요 CLI/환경변수 (버전 명시)
## How to Run         — 대표 호출 예
## Procedure          — 번호 단계, 각 단계에 검증 가능한 완료 기준
## Pitfalls           — 알려진 함정
## Verification       — 성공 증명 방법
## Install (agent-readable)   — §4 자가설치 절차 (의무)
## Output Contract    — §3으로 위임했다면 그 취지 한 줄
```

규칙:
- 각 절차 단계는 **검증 가능한 완료 기준**으로 끝난다 ("요약하라" ✗, "수정된 파일
  전수 나열" ○).
- 하네스 고유 도구명을 코어에 직접 쓰지 않는다. 비전 읽기 같은 하네스 종속 단계는
  "영상 프레임을 네이티브 비전 도구로 읽는다"라고 기술하고, 구체 도구는 어댑터
  테이블(§5)이 매핑한다.
- 머신 로컬 절대경로 금지. repo-relative 또는 `~` 경로만.

### 2.3 폴더 구조 (자기완결 원칙)

```
<skill-name>/
├── SKILL.md            # 코어 (§2.2)
├── scripts/            # 실행기 (하네스 무관한 파이썬/셸)
├── references/         # 부가 문서 (SKILL.md 본문은 100-200줄 유지)
└── templates/          # 출력 템플릿 (예: 컷별 4칸 표)
```

**스크립트 동거 필수**: SKILL.md와 scripts/는 반드시 같은 폴더 단위로 복사 가능해야
한다. claude-video의 사후 분석 — scripts가 분리돼 배포되면 비-Claude 호스트에서
스킬이 dead on arrival이었다.

---

## 3. 출력 계약 레이어 (페르소나 분리)

기술 절차와 출력 규격은 다른 레이어에 둔다. 근거: claudewatch 릴스의 실측 프롬프트 —

> "스킬이 영상 분석 결과를 낼 때는 항상 한국어로, 아래 형식을 따르게 SOUL.md에
> 명시해줘. - 후킹 멘트만 따로 강조해서 제일 위에 - 컷별 표: 타임스탬프/화면에
> 보이는 것/화면 텍스트/실제 대사 - '왜 이 구조가 먹히는지' 분석 - '내 콘텐츠에
> 적용할 점' 제안"

이 지시의 요체는 스킬이 아니라 **페르소나 계층에 기록하는 출력 계약**이다.
스킬은 여러 개여도 보고서 형식은 일관된다.

하네스별 페르소나 레이어 매핑:

| 하네스 | 페르소나/행동 규칙 파일 |
|---|---|
| Claude Code | CLAUDE.md (전역: ~/.claude/CLAUDE.md) |
| Codex CLI | AGENTS.md (전역: ~/.codex/AGENTS.md) |
| OpenCode | AGENTS.md / opencode.json rules |
| Hermes | SOUL.md (프로필별) |

규칙:
- 출력 계약이 스킬 고유하면 스킬 본문 `## Output Contract`에 둔다.
- 여러 스킬이 공유하는 프로젝트 공통 형식(언어, 표 양식, 강조 규칙)이면 페르소나
  레이어에 두고, 스킬 본문에서 "보고서 형식은 페르소나 계약을 따른다"고 참조만 한다.
- 컷별 4칸 표(타임스탬프/화면/화면텍스트/대사)처럼 데이터 스키마를 강제하는 형식은
  templates/에 파일로 동봉하고 본문에서 참조한다 — 형식 명시가 곧 데이터 스키마
  명시다 (프레임+자막을 시간축 조인 가능하게 유지하라는 요구사항으로 번역됨).

---

## 4. 자가설치 프로토콜 (핵심 장)

스킬은 자신의 설치 절차를 본문에 기술한다. 에이전트는 이것을 읽고 실행한다.

### 4.1 `## Install (agent-readable)` 의무 섹션

```markdown
## Install (agent-readable)

1. Detect your harness:
   - Claude Code → ~/.claude/skills/
   - Codex CLI  → ~/.codex/skills/
   - OpenCode   → ~/.config/opencode/skills/ (or ~/.agents/skills/)
   - Hermes     → run: hermes skills install <hub-path-or-url>
2. Copy this entire folder (SKILL.md + scripts/ + references/ + templates/)
   into the detected path. Folder name must equal frontmatter `name`.
3. Install prerequisites and REPORT VERSIONS:
   yt-dlp --version; ffmpeg -version | head -1
4. Verify: run scripts/analyze_video.py --selftest
   Expected: exit 0 and frames/ + transcript.txt created.
5. Report back: installed path + tool versions + selftest result.
```

### 4.2 에이전트 설치 루프 (표준 절차)

에이전트가 스킬을 도입할 때의 표준 흐름:

1. **하네스 감지**: 자신의 스킬 탐색 경로 존재 여부로 판별 (예: `~/.hermes/` 존재 → Hermes)
2. **경로 결정**: 어댑터 테이블(§5)에서 설치 대상 경로 조회
3. **설치**: 폴더 전체 복사 (Hermes는 `hermes skills install`로 보안 스캔 경유)
4. **의존성 설치 + 버전 보고**: yt-dlp/ffmpeg/whisper 등 실제 버전 출력을 그대로 보고
5. **검증 게이트**: 스킬이 제공하는 selftest 또는 소규모 실데이터 시험 실행
6. **완료 보고**: 설치 경로 + 도구 버전 + selftest 결과 3종 세트

### 4.3 안전 규칙

- 설치 대상은 하네스의 표준 스킬 경로로 한정. 시스템 설정·다른 도구의 설정 파일
  수정은 스펙 위반.
- 의존성 설치(pip/npm)는 스킬이 요구 버전을 명시하고, 에이전트는 설치 후 실제
  버전을 확인해 보고한다 ("설치했다"가 아니라 `--version` 출력으로 증명).
- 검증 게이트 실패 시: 1회 재시도 → 실패하면 사용자에게 블록 보고. 무리한 우회
  금지.
- Hermes처럼 스킬 쓰기 승인 게이트(`skills.write_approval`)가 있는 하네스는 그
  게이트를 존중한다.

### 4.4 근거: 왜 "설치 검증 보고"를 표준화하는가

릴스 실측 프롬프트의 "설치 끝나면 실제로 뭐가 깔렸는지 (yt-dlp, ffmpeg, 음성인식
도구 버전) 확인해서 결과 알려줘"는 단순한 친절 기능이 아니라 **신뢰 모델**이다:
에이전트의 완료 주장을 산출물(도구 버전 출력, selftest exit code)로 담보한다.
이것을 모든 범용 스킬의 의무 단계로 채택한다.

---

## 5. 하네스 어댑터 테이블

### 5.1 스킬 탐색 경로 (공식 문서 기준, 2026-09 검증)

| 하네스 | 전역 | 프로젝트 | 출처 |
|---|---|---|---|
| Claude Code | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` | anthropic 문서 |
| Codex CLI | `~/.codex/skills/<name>/` | `.codex/skills/<name>/` | agensi/ITECS 가이드 |
| OpenCode | `~/.config/opencode/skills/<name>/` | `.opencode/skills/<name>/` | opencode.ai/docs/skills (공식) |
| OpenCode (호환) | `~/.claude/skills/`, `~/.agents/skills/` 도 읽음 | `.claude/skills/`, `.agents/skills/` | 공식 문서 확인 |
| Hermes | `~/.hermes/skills/<category>/<name>/` | `<project>/.hermes/skills/`, `.agents/skills/` | hermes 공식 문서 |

**공용 디렉토리 발견**: `.agents/skills/`는 OpenCode와 Hermes가 모두 읽는 크로스툴
경로다. 최대 호환성을 원하면 **`~/.agents/skills/<name>/` 단일 복사로 OpenCode+Hermes
동시 커버**가 가능하다. Claude Code와 Codex는 각자 경로가 필요하다.

### 5.2 트리거 방식

| 하네스 | 스킬 로딩 방식 | 트리거 |
|---|---|---|
| Claude Code | 스킬 인덱스 시스템 프롬프트 노출 → 모델 판단 로드 | description 매칭 (자율) 또는 /스킬명 |
| Codex CLI | skills 디렉토리 스캔 | description 매칭 (자율) |
| OpenCode | `skill` 도구로 on-demand 로드, available_skills 목록 제공 | description 매칭 + permission 설정 가능 |
| Hermes | skills_list/skill_view 도구 | description 매칭 (자율) |

공통 함의: **description이 사실상 유일한 트리거 인터페이스**다. 그래서 §2.1의
57자 규칙이 중요하다. 우발적 토큰 소모가 우려되는 무거운 스킬은 OpenCode의
permission `ask`, 또는 본문에 "슬래시 명령으로만 호출" 가드를 권장한다
(watch-video-skill의 선례).

### 5.3 도구 능력 매핑 (비전 읽기 등)

| 능력 | Claude Code | Codex CLI | OpenCode | Hermes |
|---|---|---|---|---|
| 이미지 읽기 | Read (멀티모달) | 확인 필요 | 모델 의존 | vision_analyze (네이티브) |
| 셸 실행 | Bash 도구 | 셸 네이티브 | 셸 | terminal |
| 웹 추출 | WebFetch 등 | 네이티브 | 네이티브 | web_extract |

스킬 작성자는 능력 차이가 있는 단계(예: 프레임 읽기)에 분기를 둔다:
"네이티브 비전 도구가 있으면 그것으로, 없으면 프레임을 모델 컨텍스트에 직접
첨부 가능한 경로로 전달" 식으로.

---

## 6. 준수 예시: video-watch 스킬

이번 조사·구현으로 검증된 릴스 분석 파이프라인(utd-dlp → ffmpeg 장면전환 프레임 →
faster-whisper 자막 → index.json)을 첫 준수 사례로 채택한다.

- 검증 완료: 페이스북 릴스 원본 28.5초에서 프레임 7장 + 타임스탬프 자막 추출 성공
- scripts/analyze_video.py가 §2.3의 scripts/ 동거 원칙과 §4.1의 selftest 요건을
  충족 (selftest 플래그는 v0.2에서 추가 예정)
- 출력 계약(컷별 4칸 표)은 templates/cut-table.md로 동봉하는 것을 권장

---

## 7. 트레이드오프와 미해결 과제

1. **자가설치의 신뢰 경계**: 에이전트가 셸을 실행해 설치하려면 권한이 필요하다.
   §4.3으로 완화하지만, 하네스별 샌드박싱 정책 차이는 계속 추적 필요.
2. **Codex 비전 능력 미확인**: §5.3에서 "확인 필요"로 남겨둔 항목. 실측 전까지
   video-watch의 Codex 지원은 부분 지원으로 표기해야 함.
3. **표준안 버전 관리**: metadata.spec 필드로 준수 버전을 명시하게 했으나, 위반
   검증기(linter)는 별도 과제. Hermes validator를 확장하는 방안 검토 가능.
4. **GPT(웹 ChatGPT) 계열**: 셸이 없는 환경에서는 자가설치 자체가 불가 — 이
   표준안의 범위를 "셸 보유 에이전트"로 한정하는 것이 정당해 보인다 (§0 목표
   정의와 일관).

---

## 8. 후속 작업 (제안)

- [ ] 승우님 피드백 반영 → v0.2
- [ ] video-watch 스킬을 본 표준안으로 리팩터링 (scripts/ + templates/ 동봉형)
- [ ] §5.3 Codex 비전 능력 실측
- [ ] 준수 검증 스크립트 초안 (frontmatter + 필수 섹션 체크)
