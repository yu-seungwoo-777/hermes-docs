# 조사 보고서: Hermes + Superpowers 기반 에이전틱 코딩 체계

- 작성: agentarch (에이전틱 코딩 설계 전문가)
- 날짜: 2026-09-03 (UTC)
- 요청자: 승우님
- 목적: "hermes + superpowers로 에이전틱 코딩 수행. 리드 세션 glm-5.3 / 구현 세션 glm-5.3-flash 분리 운영. 신규 프로필 구현 여부, 서버 외부 작업 여부 판단을 위한 자원 조사."

---

## 1. 사용 가능 자원 실측 결과

### 1.1 Hermes 프로필 / 게이트웨이 (실측)

| 프로필 | 모델 | 게이트웨이 | 역할 |
|---|---|---|---|
| default | glm-5.3-flash (zai) | running | 최상위 오케스트레이터 |
| agentarch | glm-5.3-flash (zai) | running | 에이전틱 코딩 설계 (본 프로필) |
| biseo-jaeyoung | glm-5.3-flash (zai) | running | 재영님 비서 |
| dokploy | glm-5.3-flash (zai) | running | 인프라/Dokploy |
| news | glm-5.3-flash (zai) | running | 뉴스 브리핑 |

- 칸반 오케스트레이션 가동 중: dispatcher 60s tick, `orchestrator_profile=default`, 자동분해 ON, 리뷰 디스패치 ON, stale 타임아웃 4h.
- 전 프로필이 동일 모델(glm-5.3-flash) — **리드/구현 모델 분리는 현재 없음. 리드용 glm-5.3 프로필이 이번에 신설 필요한 부분.**

### 1.2 superpowers 관련 자원 (실측)

- Claude Code CLI **미설치** (`claude: command not found`). Codex/OpenCode도 없음.
- 단, **superpowers 파생 스킬이 이미 전 프로필에 이식되어 있음** (`adapted from obra/superpowers`):
  - `software-development/test-driven-development`
  - `software-development/systematic-debugging`
  - `software-development/plan`
  - `software-development/requesting-code-review`
- 즉 superpowers의 핵심 **방법론(TDD·디버깅·플랜·리뷰)은 이미 Hermes 스킬 체계로 내재화**된 상태. 빠진 것은 superpowers의 나머지 스킬(brainstorming, executing-plans, subagent-driven-development, using-git-worktrees 등)과 Claude Code 플러그인 런타임.

### 1.3 모델 공급 (zai coding endpoint 실측)

- `https://api.z.ai/api/coding/paas/v4` — 모델 목록 실측: `glm-4.5, 4.5-air, 4.6, 4.7, 5, 5-turbo, 5.1, 5.2, glm-5.3, glm-5.3-flash`.
- **glm-5.3 / glm-5.3-flash 모두 동일 API 키로 즉시 사용 가능.** 별도 계약·키 추가 불필요.
- glm-5.3 응답 실측: reasoning token을 명시적으로 소모(추론형) — 리드 역할(설계·분해·검토)에 적합. flash는 경량 고속 — 구현 반복에 적합.

### 1.4 기타 환경

- Anthropic 호환 엔드포인트(`api.z.ai/api/anthropic/v1/messages`) **동작 확인** → zai 키만으로 Claude Code를 구동할 수 있는 경로가 실재함 (`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` 방식).
- Node v26.7.0, git 2.43.0 있음. **tmux 없음**(대화형 에이전트 구동 시 필요), 디스크 여유 23G.

---

## 2. 리드(glm-5.3) / 구현(glm-5.3-flash) 분리 설계 — 3개 대안 비교

### 대안 A. Hermes 칸반 + 리드 전용 신규 프로필 (권장)

```
default (승우님 지휘)
  └─ codinglead (신규, model.default=glm-5.3)  ← 리드: 계획·분해·스펙·검토
       ├─ (칸반 태스크) 구현 워커 = 기존 프로필(glm-5.3-flash) 또는 신규 coder 프로필
       └─ 리뷰 게이트 = codinglead가 request_changes/완료 판정
```

- **리드 = 신규 프로필 1개**(`hermes profile create codinglead` → model만 glm-5.3으로 설정). 구현은 기존 flash 프로필을 그대로 재활용하거나 전용 coder 프로필 신설.
- 분리 방식: 칸반 카드 본문에 스펙을 담는 **이미 검증된 패턴** (본 문서 체계가 하던 방식 그대로). 리드는 카드를 쓰고, 구현 워커는 카드를 읽고 실행, 리드가 결과를 검토.
- 장점: 기존 인프라 100% 재사용, 보고/검증/가드레일 체계 그대로 적용, 토큰 비용 통제 가능(cron-cost-audit 노하우 존재), 모델 오버라이드는 프로필별 config로 깔끔히 분리.
- 단점: superpowers의 대화형 brainstorming/인터랙티브 플랜 UX는 없음(칸반 비동기로 대체됨). 리드 프로필 신설·SOUL.md·명단 등재 작업 필요.

### 대안 B. Claude Code + superpowers 플러그인 (서버 내)

- zai Anthropic 호환 확인됨 → `claude` CLI 설치 후 zai 키로 구동 가능(추정 — 실구동 검증 전).
- 리드/구현 분리는 Claude Code의 subagent(Plan mode → implement)로 표현 가능하나, **모델별 역할 고정이 번거로움**: Claude Code는 단일 `ANTHROPIC_MODEL` 기반이며, subagent별 모델 지정은 GLM의 Anthropic 호환 레이어의 model alias 지원 여부에 종속(미검증).
- 장점: superpowers 원본 워크플로우(브레인스토밍→플랜→TDD 서브에이전트→리뷰) 그대로 사용.
- 단점: tmux 부재 설치 필요, superpowers 스킬들이 Claude 전용 훅/커맨드에 결합되어 GLM 환경에서의 호환성 불확실, Hermes 칸반과 **별도의 제2 오케스트레이션 체계**가 생겨 관리 비용 2배. 이미 Hermes 스킬로 이식된 방법론과 중복.

### 대안 C. 서버 외부(승우님 로컬 PC)에서 Claude Code + superpowers

- 승우님 PC에 Claude Code 설치 → superpowers 마켓플레이스 설치 → zai 키(`ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic`) 연결.
- 장점: superpowers의 인터랙티브 세션 경험을 가장 온전히 살릴 수 있는 경로. 리드 작업(설계 대화, 브레인스토밍)을 로컬에서, 구현을 서버 칸반에 맡기는 **하이브리드도 가능**.
- 단점: 서버 측 자동화(칸반·크론·리뷰 게이트)와 단절 — 별도 수동 연계 필요. 로컬 환경은 본 조사 범위 밖(미검증).

### 비교 요약

| 기준 | A. 칸반+신규 리드 프로필 | B. 서버 내 Claude Code | C. 외부 Claude Code |
|---|---|---|---|
| 리드/구현 모델 분리 | 명확 (프로필 단위) | 불확실 (미검증) | 불확실 (미검증) |
| 기존 체계 재사용 | 최대 | 낮음 (이원화) | 낮음 |
| superpowers 방법론 | 이미 이식된 4스킬 + 추가 이식 가능 | 원본 그대로 | 원본 그대로 |
| 도입 비용 | 낮음 (프로필 1개) | 중~높음 (tmux, 호환 검증) | 낮음~중 (로컬 작업) |
| 자동화·보고 연계 | 원래 체계 | 이원화 비용 | 수동 연계 |

---

## 3. 권장안

**대안 A를 축으로, 필요시 C를 보조로 하는 하이브리드.**

1. `codinglead` 프로필 신설 (glm-5.3, 리드 전담: 스펙·분해·검토 게이트). 구현은 기존 flash 프로필/워커가 수행.
2. superpowers에서 아직 이식 안 된 스킬 중 필요한 것(`executing-plans`, `subagent-driven-development`, `using-git-worktrees` 등)을 Hermes 스킬로 추가 이식 — Claude Code 런타임 없이 방법론만 취함.
3. 서버 외부 Claude Code는 승우님이 대화형 설계 세션을 직접 하고 싶을 때의 선택지로 남김 (zai 키 연결 경로는 실측으로 유효 확인 완료).

### 후속 작업 (승우님 결정 필요)

- [ ] codinglead 프로필 신설 승인 → default 오케스트레이터가 생성·전문화·명단 등재 (agentarch 직접 수행 범위 아님)
- [ ] 구현 전용 워커를 신설할지, 기존 프로필(dokploy 등) 겸직할지
- [ ] superpowers 추가 스킬 이식 대상 선정
- [ ] 서버 외부 Claude Code 병행 여부

## 4. 검증 근거

- zai `/models` 목록, glm-5.3 chat 응답, Anthropic 호환 `/v1/messages` 응답: 2026-09-03 실측 curl (키 평문 미출력).
- 프로필/게이트웨이: `hermes profile list`, `hermes gateway list` 실측.
- 칸반 설정: `hermes config get kanban` 실측.
- superpowers 파생 스킬: 프로필별 skills 디렉터리 grep 실측 (16개 매치).
