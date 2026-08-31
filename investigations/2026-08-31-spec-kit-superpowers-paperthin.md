# 에이전틱 코딩 프로젝트 3종 심층 조사: spec-kit · paperthin · superpowers

- **조사일**: 2026-08-31
- **조사 방법**: 각 저장소를 실제 클론(`git clone --depth 1`)해 소스 코드·스크립트·훅·CI를 직접 분석 (README 열람 수준을 넘어 동작 검증). 활동성 수치는 GitHub REST API(`gh api`) 실측.
- **조사 경로**: 3개 독립 서브에이전트 병렬 조사 후 취합. 근거 파일 경로는 각 절 말미의 "근거" 참조.

---

## 요약 비교

| 항목 | spec-kit (github) | superpowers (obra) | paperthin (LilMGenius) |
|---|---|---|---|
| 한 줄 정의 | 스펙 주도 개발(SDD) 툴킷 + `specify` CLI | 코딩 에이전트용 개발 방법론 플러그인 | "제거/정리" 방향의 마크다운 스킬 28개 모음 |
| 핵심 산출물 | Python CLI + 마크다운 커맨드 템플릿 + 스크립트 헬퍼 | 14개 SKILL.md + SessionStart 훅 | 28개 SKILL.md (실행 코드 거의 없음) |
| 접근 방식 | 결정적 스크립트 + LLM 지시문 주입 | 부트스트랩 스킬 강제 주입 → 스킬 자동 트리거 | 순수 절차 지시문 (에이전트 불가지론적) |
| 버전 | v1.0.1 (2026-08-21) | v6.3.0 (2026-08-12) | v0.17.4 (2026-08-18) |
| 스타 / 포크 | 132,363 / 11,912 | 279,695 / 25,072 | 914 / 97 |
| 최근 push | 2026-08-28 | 2026-08-29 | 2026-08-18 |
| 지원 에이전트 | 30+ 통합 (Copilot 기본) | 14+ 하네스 (Hermes Agent 포함) | Claude Code / Codex / OpenCode |
| 라이선스 | MIT | MIT | MIT |

세 프로젝트 모두 "AI 코딩 에이전트에게 절차·규율을 부여한다"는 같은 문제를 다른 층위에서 푼다: **spec-kit은 아티팩트 파이프라인**(스펙→계획→태스크→구현), **superpowers는 프로세스 강제**(세션 부트스트랩 + 스킬 자동 트리거), **paperthin은 산물 정제**(만들어진 코드의 축소·정리).

---

## 1. github/spec-kit

### 개요
GitHub 공식 Spec-Driven Development(SDD) 툴킷. "스펙이 실행 가능하다"는 철학 아래, 자연어 기능 설명 → 스펙 → 기술 계획 → 작업 분해 → 구현 → 수렴(converge)의 파이프라인을 임의의 AI 코딩 에이전트 위에서 돌린다. 핵심 구성물: ① uv/pip로 설치하는 Python CLI `specify`(패키지명 specify-cli, Typer 기반) ② 에이전트에 주입되는 마크다운 커맨드/스킬 템플릿(`templates/commands/*.md`) ③ Bash/PowerShell/Python 3종 스크립트 헬퍼 ④ 워크플로우 엔진·확장(extension)·프리셋·번들 시스템.

### 동작 원리
"LLM에게 지시문을 주입하고, 결정적(deterministic) 작업은 셸 스크립트에 위임"하는 이중 구조.

1. `specify init <프로젝트> --integration <agent>` 실행 시 `.specify/` 디렉터리에 템플릿·스크립트·워크플로우를 설치하고(`.specify/templates/{spec,plan,tasks,constitution,checklist}-template.md`, `.specify/scripts/{sh,ps,py}`, `.specify/memory/constitution.md`, `.specify/workflows/speckit/workflow.yml`), 선택한 에이전트의 컨벤션에 맞게 커맨드 파일을 변환해 주입한다(예: claude → `.claude/skills/speckit-<cmd>/SKILL.md`, copilot → `.github/.../speckit.<cmd>.agent.md`).
2. 각 커맨드 템플릿은 YAML frontmatter(description, scripts, handoffs) + 본문으로 구성되며, `{SCRIPT}` 플레이스홀더로 스크립트를 호출하고 `$ARGUMENTS`로 사용자 입력을 받는다.
3. 스크립트는 파일 경로 계산·브랜치 생성·템플릿 복사 같은 비-LLM 작업을 JSON으로 반환한다(예: `check-prerequisites.sh --json --require-tasks` → `{"FEATURE_DIR":"...","AVAILABLE_DOCS":[...]}`).
4. 확장 훅은 `.specify/extensions.yml`의 `hooks.before_specify/before_plan/before_tasks/before_implement` 키를 각 커맨드 템플릿이 읽어 선택/강제 실행한다.

### 사용자 워크플로우 (소스 검증)
- **[0] `/speckit-constitution`** — `constitution-template.md`를 `.specify/memory/constitution.md`로 생성. 프로젝트 헌법(불변 원칙) 시딩.
- **[1] `/speckit-specify`** — 기능 설명($ARGUMENTS)에서 2-4단어 short name 생성(`user-auth` 등), 스크립트로 브랜치 생성, `specs/<NNN>-<short-name>/`에 spec.md 생성, 경로를 `.specify/feature.json`에 기록(하위 커맨드가 브랜치명 없이 기능 디렉터리를 찾도록 함). 스펙 템플릿은 P1/P2 우선순위의 독립 검증 가능한 사용자 스토리 + Given/When/Then 수용 시나리오 구조를 강제.
- **[2] `/speckit-plan`** — `setup-plan.sh --json` 실행으로 plan.md 생성, Technical Context 작성, constitution 체크 게이트 평가, Phase 0 `research.md`(NEEDS CLARIFICATION 해소), Phase 1 `data-model.md`/`contracts/`/`quickstart.md` 생성.
- **[3] `/speckit-tasks`** — plan.md(필수)+spec.md(필수)+선택 아티팩트를 읽어 사용자 스토리별로 정렬된 `tasks.md` 생성(Setup→Foundational→스토리별 Phase→Polish, 의존성 그래프·병렬 실행 예시 포함).
- **[4] `/speckit-implement`** — `check-prerequisites.sh --json --require-tasks`로 선행조건 검증, checklists/ 스캔해 미체크 항목 있으면 정지·사용자 확인(읽기 전용 게이트), 전체 아티팩트를 읽고 작업을 단계별 실행.
- **선택 단계**: `/speckit-clarify`(계획 전), `/speckit-analyze`(작업 후 일관성 검사), `/speckit-checklist`, 그리고 v1.0 신설 `/speckit-converge`(스펙 대비 구현 수렴, Converged까지 반복).

### 아키텍처
- **철학**: "코드가 왕이던 시대를 뒤집는다" — 스펙을 폐기하는 부산물이 아니라 실행 가능해지는 1급 산출물로 만들고, intent→spec→plan→tasks→implementation으로 정제하며 각 단계에 게이트(constitution check, checklist gate, analyze 일관성)를 둔다.
- **템플릿 엔진**: 전통적 템플릿 엔진이 아니라 **"마크다운 프롬프트 컴파일"** 방식. `templates/commands/*.md`의 canonical 템플릿을 통합(registrar)이 에이전트별 포맷으로 변환. base.py의 4개 기본 클래스(MarkdownIntegration/TomlIntegration/YamlIntegration/SkillsIntegration)에 서브클래스 38개가 레지스트리에 등록됨.
- **확장성**: 워크플로우 엔진(Jinja류 표현식·스텝·스위치 지원), extension 시스템(훅+커맨드+커뮤니티 카탈로그), preset, bundle, 이벤트 시스템이 계층화. CLI 서브커맨드: init/check/version/self/extension/integration/event/preset/bundle/workflow.

### 설치·요구사항
- Python ≥ 3.11. 권장: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z` 후 `specify init my-project --integration copilot`(기본 통합은 copilot). uvx/pipx도 가능. 에이전트 CLI(예: claude)는 별도 설치 필요. 스크립트 타입은 sh/ps/py 선택.
- **실행 검증**: 본 서버(uv 없음)에서 venv+pip로 소스 설치 후 `specify init /tmp/demo-proj --integration claude --script sh --non-interactive` 성공 — `.claude/skills/speckit-*/SKILL.md` 10개, `.specify/` 하위 템플릿·스크립트·constitution·workflow 생성 확인. v1.0+ wheel은 템플릿·스크립트를 core_pack으로 번들해 에어갭 설치 지원.

### 활동성
스타 132,363 / 포크 11,912 / 오픈 이슈 335. 최종 push 2026-08-28. 2025-08-21 첫 커밋 후 1년 만인 2026-08-21에 v1.0.0 도달, 최신 v1.0.1. 확장/프리셋 커뮤니티 카탈로그에 신규 항목 지속 병합, CI 다수 정비 — 매우 활발.

**근거**: README.md, spec-driven.md, src/specify_cli/commands/init.py, integrations/__init__.py(_register_builtins), integrations/base.py, integrations/{claude,copilot}/__init__.py, templates/commands/{specify,plan,tasks,implement}.md, scripts/bash/*.sh, workflows/speckit/workflow.yml, pyproject.toml (로컬 클론 /tmp/spec-kit). 실측: venv 설치 후 init 실행, GitHub API.

---

## 2. obra/superpowers

### 개요
Jesse Vincent(obra)가 만든 코딩 에이전트용 **"완전한 소프트웨어 개발 방법론"** 패키지(README 첫 줄 인용). Claude Code 플러그인이 기반이지만 Codex, Cursor, Gemini CLI, Copilot CLI, Devin, Kimi, OpenCode, Pi, Antigravity, **Hermes Agent** 등 14개+ 하네스를 공식 지원. 버전 6.3.0, MIT. 최상위 구조: skills/(14개 스킬), hooks/, .claude-plugin/(plugin.json, marketplace.json), docs/, tests/, scripts/. 핵심 아이디어는 **"스킬이 자동 트리거된다"**는 것 — 세션 시작 시 부트스트랩 스킬이 주입되어 에이전트가 모든 작업 전 관련 스킬을 확인·호출하도록 강제.

### 동작 원리 (2층 로드 메커니즘)
1. **세션 시작 주입**: `hooks/hooks.json`의 SessionStart 훅(matcher: `"startup|clear|compact"`)이 `run-hook.cmd`(Windows 배치+bash 폴리글랫 래퍼) → `hooks/session-start` bash 스크립트를 실행. 이 스크립트는 `skills/using-superpowers/SKILL.md` 전문을 읽어 JSON 이스케이프 후 플랫폼별 형식(Cursor `additional_context`, Claude Code `hookSpecificOutput.additionalContext` 등)에 맞춰 additionalContext로 출력. 즉 `<EXTREMELY-IMPORTANT>` 태그로 감싸진 부트스트랩 전문이 매 세션 시작(및 compaction 후)에 시스템 컨텍스트로 주입된다.
2. **스킬 발견**: 나머지 13개 스킬은 Claude Code 네이티브 Skill 도구로 on-demand 로드. SKILL.md의 frontmatter는 name/description 두 필드뿐이며, description은 "언제 쓰는지"를 기술하는 트리거 서술(예: TDD — "Use when implementing any feature or bugfix, before writing implementation code")로 모델이 스스로 호출하도록 유도.

부트스트랩 스킬(`using-superpowers`)은 강제 장치다: *"If you think there is even a 1% chance a skill might apply... you ABSOLUTELY MUST invoke the skill"* — 응답 전 어떤 행동보다 스킬 확인을 먼저 하라는 규칙, 합리화를 차단하는 'Red Flags' 표, 사용자 지시(CLAUDE.md) > 스킬 > 기본동작 순의 우선순위를 담는다. 하네스별 차이는 references/(codex-tools.md, hermes-tools.md 등)로 흡수.

### 사용자 워크플로우
1. **설치** — Claude Code: `/plugin install superpowers@claude-plugins-official` (또는 `/plugin marketplace add obra/superpowers-marketplace` → install). **Hermes Agent: `hermes plugins install obra/superpowers --enable`** (주의: post-compaction 훅이 없어 아주 긴 세션에서 부트스트랩 소실 가능 — 재시작 권장). 그 외 하네스는 README의 14개 섹션별 명령. 업데이트는 재설치.
2. **사용** — 설치 후 별도 조작 불필요. README의 기본 워크플로우 7단계: **brainstorming**(코드 작성 전 요구사항→설계 합의, `<HARD-GATE>`로 창작 작업 전 필수 강제) → **using-git-worktrees**(승인된 설계로 격리 워크스페이스) → **writing-plans**(2-5분 단위 bite-sized 태스크 분해, `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` 저장) → **subagent-driven-development** 또는 **executing-plans**(태스크당 신규 서브에이전트 디스패치+2단계 리뷰 / 배치 실행+휴먼 체크포인트) → **test-driven-development**("Write the test first. Watch it fail. Write minimal code to pass." RED-GREEN-REFACTOR 강제) → **requesting-code-review**(심각도별 리뷰, critical은 진행 차단) → **finishing-a-development-branch**(merge/PR/keep/discard 옵션, 워크트리 정리). 디버깅용 **systematic-debugging**은 "The Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST".
3. **커스텀 스킬 추가** — `skills/<영문-케박명>/SKILL.md` 규약(프론트매터 name, description)만 지키면 되며, 스킬 작성법 자체도 **writing-skills** 메타 스킬로 문서화. 새 하네스 포팅 가이드는 docs/porting-to-a-new-harness.md.

### 아키텍처
단일 다중-하네스 플러그인 패키지. 개념적 계층 3층: **부트스트랩**(using-superpowers, 훅으로 주입) → **프로세스 스킬**(brainstorming/debugging 등 접근법 결정) → **구현/유틸 스킬**(TDD 등 실행). 스킬 간 상호 참조로 조합(composable). 반복 패턴: 게이트(`<HARD-GATE>`), 공표(announce), 절차 단계, 합리화 차단 표. 하네스별 매니페스트: package.json(opencode/pi), gemini-extension.json. Windows는 Git for Windows의 bash 필요(없으면 훅이 조용히 건너뛰고 컨텍스트 주입만 비활성화).

### 활동성
스타 279,695 / 포크 25,072 / 오픈 이슈 339 — 3종 중 최대. 생성 2025-10-09, 최근 push 2026-08-29. 릴리스 월 1~2회 규칙적(v6.0.3 → v6.3.0). 최신 v6.3.0(2026-08-12)의 특기 사항: **"Devin CLI and Hermes Agent support, brainstorming three-path router"**. 스킬 자체 버그픽스도 활발(find-polluter.sh 등). 상업 지원 언급(sales@primeradiant.com).

**근거**: README.md(정의 L1-2, 설치 L61~265, 워크플로우 L266~278), skills/using-superpowers/SKILL.md, skills/{brainstorming,test-driven-development,systematic-debugging,writing-plans,writing-skills}/SKILL.md, hooks/{hooks.json,session-start,run-hook.cmd}, .claude-plugin/{plugin.json,marketplace.json}, package.json, gemini-extension.json, docs/porting-to-a-new-harness.md, tests/hooks/test-session-start.sh (로컬 클론 /tmp/superpowers). 실측: gh api.

---

## 3. LilMGenius/paperthin

### 개요
"에이전트 불가지론적(agentic-agnostic) 설계 패턴 스위트" — 특정 에이전트에 종속되지 않는 순수 마크다운 스킬 **28개**의 모음(v0.17.4, MIT). 풀어내는 문제: *"대부분의 에이전트 스킬은 slop(노이즈·중복·팽창)이다"* — 에이전트가 물건을 만들 때 계속 '추가'만 하고 되돌아가 지우지 않는 습관. 이에 반해 **모든 스킬이 '제거/정리' 방향으로 동작**한다(re0: 패치 대신 v0 재작성, debloat: 압축, ssotize: 사실 단일화 등). 스킬은 4개 관점으로 분류: **depth**(하나의 산물 정제, 19개)/**breadth**(여러 파일 간 일관성, 2개)/**coil**(빌드 사이클 간 학습 이월, 6개)/**mesh**(독립 관점의 수렴, 1개). GitHub 언어 통계상 Shell/JavaScript로 보이지만, 실제 '제품'은 전부 마크다운이고 JS/Shell은 설치·알림 인프라일 뿐이다.

### 동작 원리
실행 코드가 거의 없는 것이 핵심 설계다. 각 스킬은 `skills/<perspective>/<name>/SKILL.md` 하나의 마크다운 파일(YAML frontmatter + Goal/Workflow/Rules/Verification 구조)이며, "로직"은 코드가 아니라 모델이 따르는 절차 지시문이다. 예: `skills/depth/re0/SKILL.md` — "대상 산물을 처음의 깨끗한 v0처럼 다시 쓴다. 개선할 게 없으면 아무것도 바꾸지 않는다"(10단계 워크플로).

실제 코드는 3개 역할만 한다:
1. `scripts/catalog.cjs` — 28개 스킬 이름의 CATALOG 배열, 설치 위치(~/.agents/skills, ~/.claude/skills) 스캔, 누락 스킬 계산·알림 문구 생성의 단일 코드 홈.
2. `scripts/session-check.cjs` — Claude Code/Codex의 SessionStart 훅에서 **하루 1회 스로틀**(~/.re0/last-notice.json)로 누락 스킬 알림을 JSON으로 출력(실패해도 항상 exit 0).
3. `scripts/opencode-discovery.js` — OpenCode용 동일 알림의 system.transform 플러그인 어댑터.

호출 축: **user-invoked**(dedash, re0-upgrade 등 12개, `disable-model-invocation: true` — 사람만 실행) vs **model-invoked**(나머지, 모델이 자동 발동). 외부 의존성은 설치 시 npx skills CLI, 훅 런타임용 Node.js, 모델 자체뿐.

### 사용자 워크플로우
1. **설치**: `npx skills@latest add LilMGenius/paperthin --global --agent '*'` — npx skills CLI가 ~/.agents/skills에 넣고 에이전트별 디렉터리로 심링크. 부분 설치는 `-s <skill>`(re0-upgrade가 --all 사용을 금지함).
2. **갱신**: `/re0-upgrade` 스킬 — 설치 스코프 선택 → shadow-install 진단 → retire/add/refresh 계획 → 명시적 확인 → npx skills remove/add/update → 검증 → 3개 에이전트에 발견 알림 훅을 버전 고정 태그에서 자동 구성.
3. **사용**: `/re0`, `/dedash`처럼 이름으로 호출하거나 model-invoked 스킬은 자동 발동.
4. **수동 대안**: 클론 후 `bash scripts/link-skills.sh`(Claude Code용 심링크). CI는 4개 카탈로그 표면(README, plugin.json, catalog.cjs, re0-upgrade)의 동기화를 검증하고, release.yml은 태그 푸시 시 npm publish --provenance까지 자동화.

### 아키텍처 (계층 구조)
- **산물 계층**: skills/{depth 19, breadth 2, coil 6, mesh 1}/ 28개 SKILL.md — 유일한 배포물이자 로직.
- **등록 계층**: .claude-plugin/plugin.json, README 인덱스(10개 언어 번역본), re0-upgrade의 catalog — 빌드 스텝이 없어 수동 복제되며 CI가 드리프트를 감시.
- **인프라 계층**: scripts/ 3종 + 검증 스크립트 + GitHub Actions.
- **데이터 흐름**: 설치 → 에이전트가 SKILL.md를 컨텍스트로 로드 → 모델이 절차 수행. 발견 알림: 세션 시작 → 훅이 missingSkills() 실행 → 누락 시 하루 1회 알림을 모델 컨텍스트에 주입(모델이 사람에게 릴레이; **절대 자동 설치 안 함**). 런타임 상태는 ~/.re0/ 한 곳뿐.

### 활동성 및 주의점
- 생성 2026-06-19, 최종 push 2026-08-18, 총 커밋 49개, 최신 릴리스 v0.17.4(2026-08-18), 스타 914 / 포크 97 / 오픈 이슈 2. 활발한 패치 사이클. 커밋 메시지 품질이 특이할 만큼 높음(스스로의 re0-git 커밋 경제 규칙을 따름).
- README 주장과 코드의 불일치는 사실상 없음 — 카탈로그 4개 표면이 정확히 일치하고 CI가 이를 강제.
- **주의점 ①**: `re0-upgrade` SKILL.md 69행이 업그레이드 성공 후 **`gh api -X PUT user/starred/LilMGenius/paperthin --silent`로 사용자에게 알리지 않고 저장소에 자동 스타를 누르도록 지시** — README에 명시되지 않은 논란 여지 있는 동작. 채택 시 이 행을 제거/비활성화 권장.
- **주의점 ②**: 홍보성 prior-art 인용(예: Anthropic 'Fable 5/Mythos 5' 2026 링크)은 별도 검증 필요.

**근거**: package.json, .claude-plugin/plugin.json, skills/depth/re0/SKILL.md(L6-38), skills/breadth/re0-upgrade/SKILL.md(L39-103, 자동 스타 L68-69), scripts/{catalog.cjs,session-check.cjs,opencode-discovery.js,link-skills.sh}, docs/invocation.md, CLAUDE.md, .github/workflows/{ci,release}.yml, README.md (로컬 클론 /tmp/paperthin). 실측: GitHub API, npm registry.

---

## 승우님 관점 종합 (에이전틱 코딩 체계 설계자 시선)

세 프로젝트는 서로 배타적이지 않고 **보완적 층위**를 이룬다:

1. **spec-kit** — *무엇을 만들지*의 규율. 아티팩트(스펙·계획·태스크)를 파일로 남기므로 멀티에이전트 오케스트레이션과 결합하기 좋다. 칸반 체계와의 유사성: feature.json/태스크 체크리스트 ≈ 칸반 카드, checklist gate ≈ 리뷰 게이트.
2. **superpowers** — *어떻게 작업할지*의 규율. TDD·디버깅·리뷰 게이트를 스킬로 강제하는 방식은 "게이트를 스킬에 심는다"는 설계 패턴 그 자체이며, 현재 체계의 SOUL/스킬/칸반 게이트 설계와 철학이 같다. Hermes Agent 공식 지원(v6.3.0)이라 바로 실험 가능.
3. **paperthin** — *만든 것을 정제하는* 규율. '추가만 하는 에이전트' 문제에 대한 반례 집합으로, 스킬 품질 기준(단일 파일, 트리거형 description, 4관점 분류)은 스킬 라이브러리 관리 규약 설계에 참고 가치가 높다.

도입 우선순위 제안(추정): **superpowers(Hermes 네이티브 지원) → spec-kit(신규 기능 개발 파이프라인) → paperthin(필요 스킬만 선별, re0-upgrade의 자동 스타 동작 제거 후)**.

---

## 부록: 3개 동시 사용 시 충돌 분석

결론부터: **3개를 동시에 전부 활성화하면 충돌이 발생한다.** 조사 결과를 근거로 문제 지점은 다음 4가지다.

### 충돌 1. 트리거 충돌 (가장 심각)
- superpowers의 부트스트랩(`using-superpowers`)은 "적용 가능성 1%라도 반드시 스킬 호출"을 강제 주입한다. 그런데 paperthin의 model-invoked 스킬들, superpowers의 13개 스킬, spec-kit의 `/speckit-*` 커맨드가 **같은 상황을 겨냥**한다 — 계획 세우기 한 상황에 superpowers `writing-plans`와 spec-kit `/speckit-plan`, paperthin `re0`까지 동시 후보로 뜰 수 있다.
- 우선순위 규칙끼리도 겹친다: superpowers는 "사용자 지시 > 스킬 > 기본동작"을 주입하고, spec-kit은 워크플로우 엔진이 단계 순서를 강제한다 — 두 "강제 장치"가 서로를 방해한다.

### 충돌 2. 아티팩트·브랜치 충돌
- spec-kit은 `create-new-feature.sh`로 브랜치를 만들고 `specs/<NNN>-<name>/`에 산출물을 둔다. superpowers는 `using-git-worktrees`로 자기 방식의 워크트리 + `docs/superpowers/plans/`를 만든다. **두 갈래 브랜치/계획 체계가 병렬로 생기고, 둘 다 "정답 워크플로우"라고 주장**한다.

### 충돌 3. 철학 충돌 (축적 vs 제거)
- paperthin `re0`는 "패치 대신 v0 재작성", `debloat`는 산물 압축인데, spec-kit/superpowers는 스펙·계획·리뷰 문서를 계속 **축적**하는 구조다. re0가 다른 체계가 만든 산물(설계 문서, tasks.md)을 "정리" 명분으로 재작성할 위험이 있다.

### 충돌 4. 컨텍스트 예산
- 세션 시작 주입이 2겹(superpowers 부트스트랩 + paperthin 발견 알림 훅) + 스킬 description 수십 개 상주 + 프로젝트별 `/speckit-*` 10개. 스킬이 많을수록 모델의 트리거 판단 정확도가 떨어진다.

### 현실적인 조합 전략

| 층위 | 전략 |
|---|---|
| **방법론 레이어는 1개만** | superpowers 또는 spec-kit 중 **택일**. 공존 비추천 |
| **paperthin은 선별 + user-invoked만** | `re0`, `dedash` 등 12개 user-invoked 스킬만 `-s <skill>`로 설치 — 자동 트리거 자체가 없어 충돌 원천 차단 (`re0-upgrade` 자동 스타 스킬은 제외) |
| **프로젝트 단위 분리** | 신규 기능 개발(스펙 필요) 프로젝트에 spec-kit, 기존 코드 정비·리팩터링에 superpowers 스킬 — 저장소별로 설정 |

즉 "3개 다"가 아니라 **"역할별로 1+α"**가 답이다: 방법론 1개(강제력 있는 것) + paperthin은 손으로만 부르는 정제 도구로 취급. 특히 spec-kit과 superpowers의 계획/태스크 단계가 겹치는 것은 구조적이라, 함께 켜는 순간 어느 쪽 워크플로우를 따를지 모델이 매번 판단하게 된다.

---

*조사: agentarch 프로필 — 3개 독립 서브에이전트 병렬 심층 조사(소스 클론 + CLI 실행 검증 + GitHub API 실측), 2026-08-31.*
