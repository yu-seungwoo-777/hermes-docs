# Hermes 공용 워크스페이스 구조 설계 (상위 오케스트레이션 실행용)

- **날짜**: 2026-09-16
- **작성**: agentarch (에이전틱 코딩 설계 자문)
- **대상**: 오케스트레이터(default)가 워커 프로필 전체에 적용할 산출물 구조
- **근거**: 2026-09-16 실측 점검(2026-09-16-hermes-outputs-structure-audit.md) — outputs 미구현, 산출물 4곳 분산 확인

---

## 1. 설계 원칙 (5계층 모델)

```
받은 것 → 만드는 중 → 완성 → 보관 → 열람
inbox  →  work    → outputs → archive → (Telegram/웹/Syncthing)
```

1. **원본은 outputs 하나** — 채널 첨부·Mac 사본·미래 NAS는 전부 사본.
2. **삭제 금지, 이동만** — Sync 도구 도입 시 삭제 전파 문제를 구조적으로 차단.
3. **규약은 폴더에 붙인다** — `/root/workspace/AGENTS.md` 하나로 Hermes·Claude Code·Codex 전부 자동 준수 (AGENTS.md는 디렉터리 기준 재귀 로드).
4. **태스크 격리는 칸반이, 산출물 소속은 outputs가** — 칸반 t_* 워크스페이스는 작업 공간으로 유지, 최종물만 outputs로.
5. **열람 계층은 outputs만 마운트** — 웹 브라우저·Syncthing·(미래)NAS가 붙을 곳은 outputs 단 하나. work·inbox 노출 금지.

---

## 2. 디렉터리 구조

```
/root/workspace/                        ← 단일 원본 저장소 (전 프로필 공용)
│
├── AGENTS.md                           ← 규약 §4 참조 (자동 로드됨)
│
├── inbox/                              ← 받은 원자료 (영속)
│   └── YYYY-MM-DD-<출처>/              ex) 2026-09-16-telegram/
│
├── work/                               ← 진행 중 (언제든 폐기 가능)
│   └── YYYY-MM-DD-<주제>/              ex) 2026-09-16-pvc-storyboard/
│
├── outputs/                            ← 최종 산출물 ★ (사람이 보는 것)
│   └── YYYY-MM-DD-<주제>/              ex) 2026-09-16-pvc-storyboard/
│       ├── README.md                   ← 필수: 목적/생성파일/요약
│       ├── storyboard.pdf
│       ├── preview.png
│       └── ...
│
└── archive/                            ← 완료·정리 이동 (삭제 없음)
    └── YYYY-MM/                        ex) 2026-09/
```

### 배경: inbox가 필요한 이유
현재 메신저 업로드 파일은 `~/.hermes/document_cache/`에 **24시간 TTL**로 보관됨(공식 문서 확인). 승우님이 Telegram으로 보내는 원자료(PDF, 참고이미지)가 사라지는 구조적 갭 — inbox가 그 자리를 대신함. (upstream 이슈 #531이 아직 미채택이므로 자체 해결)

### 기존 영역과의 경계
| 영역 | 역할 | 변경 |
|---|---|---|
| `/root/.hermes/kanban/workspaces/t_*` | 태스크 실행·격리 (git worktree 등) | 유지 — 산출물만 outputs로 복사/작성 |
| `/root/reports` (hermes-docs) | **문서 보고서** 전용 (GitHub 동기화) | 유지 — 코드·바이너리 산출물과 역할 분리 |
| `/root/.hermes/profiles/*/` | 프로필 내부 상태 | 유지 — 산출물 저장소로 쓰지 않음 |

판별 규칙: **"사람이 읽는 기록" → reports, "사람이 쓰는 결과물" → outputs.**

---

## 3. 파일 흐름 (태스크 라이프사이클)

```
[태스크 수신]
  오케스트레이터가 칸반 태스크 생성
   ├─ 원자료가 있으면: inbox/YYYY-MM-DD-<출처>/에 저장 후 경로를 태스크 본문에 명시
   └─ 태스크 본문에 work/ 경로 지정: /root/workspace/work/YYYY-MM-DD-<주제>/

[작업]
  워커가 work/(또는 칸반 워크스페이스)에서 작업

[완료]
  워커가 최종 파일을 outputs/YYYY-MM-DD-<주제>/에 작성
   ├─ README.md 동봉 (목적·파일 목록·요약)
   └─ kanban_complete(summary=..., artifacts=[outputs 경로들])
        → 채널(Telegram) 완료 알림에 파일 첨부  ← 열람 1차 경로

[정리]
  태스크 종료 후 work/ 폴더는 archive/YYYY-MM/로 이동 (기본) 또는 폐기 (본문 지시 시)
```

---

## 4. AGENTS.md 전문 (그대로 복사해 사용)

```markdown
# /root/workspace 규약

이 디렉터리에서 작업하는 모든 에이전트(Hermes·Claude Code·Codex 포함)는 다음을 준수한다.

## 위치 규칙
1. 받은 원자료는 `inbox/YYYY-MM-DD-<출처>/`에 저장한다.
2. 작업 중간 파일은 `work/YYYY-MM-DD-<주제>/`에만 둔다.
3. 최종 산출물은 `outputs/YYYY-MM-DD-<주제>/`에 작성한다.
   - 폴더명 날짜는 산출물 완성일 기준.
4. `/root` 직하위, 홈 디렉터리, `.hermes` 내부에 산출물을 만들지 않는다.
5. 다른 태스크의 work/·outputs/ 폴더를 임의로 수정하지 않는다.

## outputs 폴더 필수 구성
outputs/YYYY-MM-DD-<주제>/ 에는 반드시 README.md를 동봉한다:
- 작업 목적 (1~3문장)
- 생성한 파일 목록과 각 파일 설명
- 주요 내용 요약

## 보존 규칙
6. outputs·inbox의 파일을 삭제하지 않는다. 정리는 `archive/YYYY-MM/`로 이동한다.
7. work/는 태스크 종료 후 오케스트레이터 지시에 따라 이동 또는 폐기한다.

## 전달 규칙
8. 완료 보고 시 산출물 절대경로를 응답 본문에 명시한다 (채널 자동 첨부).
   칸반 워커는 kanban_complete(artifacts=[...])에 outputs 경로를 넣는다.
9. README.md에는 사용자가 첨부만 보고도 판단할 수 있을 만큼의 요약을 담는다.
```

---

## 5. 역할 분담 (오케스트레이션 관점)

| 주체 | 임무 |
|---|---|
| **오케스트레이터** | ① 구조 일회성 생성 + AGENTS.md 설치 ② 태스크 본문에 work/ 경로·원자료 inbox 경로 명시 ③ 주 1회 compliance 점검(outputs 밖 신규 산출물 탐지) ④ 월 1회 archive 스위프 cron |
| **워커 프로필** | 규약 준수 + kanban_complete(artifacts) — 별도 학습 불필요 (AGENTS.md가 자동 로드) |
| **열람 계층 (미래)** | Syncthing/웹 브라우저는 `/root/workspace/outputs`만 마운트. 이 설계의 마운트 포인트는 여기 하나뿐 |

---

## 6. 오케스트레이터 실행 태스크 (붙여쓰기용)

```markdown
[태스크] 공용 워크스페이스 구조 생성

1. /root/workspace/ 하위에 inbox/ work/ outputs/ archive/2026-09/ 생성
2. 설계 문서 §4의 AGENTS.md 전문을 /root/workspace/AGENTS.md로 저장
3. /root 직하위 기존 산출물 이동:
   - kid_drawing.png, adult_20*.png → workspace/archive/2026-08/misc/
   - video-watch.zip → workspace/archive/2026-09/
   - protest-page/, mailto-test/, docs/, outbox/ → workspace/archive/ (원형 유지)
   - 빈 Sync/ 삭제
4. reports/state-db-repair/ → /root/attic/state-db-repair/ 이동 (git 제외)
5. daily 미커밋 86건: 각 프로필이 자기 파일 커밋·푸시 (또는 오케스트레이터 일괄)
6. 이후 모든 신규 태스크 본문에 work/·outputs/ 경로 명시 시작
```

---

## 7. 변형 구조 평가 (2026-09-16 승우님 제안안)

제안: `/home/hermes/{workspace/{projects,research,drafts}, outputs/{YYYY-MM-DD/}}`

| 요소 | 판정 | 사유 |
|---|---|---|
| `/home/hermes` | 조건부 채택 | 전용 사용자 분리를 계획하면 최적. 현재 Hermes는 root 실행이므로 분리 계획이 없으면 `/root/workspace`가 실체에 맞음 (사용자 분리 = 인프라 변경, 오케스트레이터 결정 사항) |
| workspace 2분리 뼈대 | ✅ 채택 (본 설계와 동일) | — |
| projects/research/drafts 분류 | ❌ 기각 → `work/YYYY-MM-DD-<주제>/` 통합 | 태스크마다 분류 판단 강요 + 시간이 지나며 재분류 이동 발생. 날짜+주제는 판단 없이 기계 적용. research는 inbox와 역할 겹침 |
| `outputs/YYYY-MM-DD/` 날짜-only | ⚠️ 보정 → `YYYY-MM-DD-<주제>/` | 같은 날 이질적 태스크 결과물이 한 폴더에 혼재하는 실패 모드. Syncthing 선택 동기화(주제 단위) 불가. 주제 접미사 1단계로 해소 |
| inbox·archive 부재 | ❌ 보강 필요 | inbox 부재 = document_cache 24h TTL 갭 방치. archive 부재 = 삭제 금지 원칙의 이동처 없음 (Syncthing 삭제 전파 문제) |

결론: 뼈대(작업/결과물 2분리, outputs 단일 창구)는 채택하되 분류 택소노미와 날짜-only outputs 두 지점을 본 설계 기준으로 보정.

---

## 8. 트레이드오프·대안 검토

| 대안 | 기각/채택 사유 |
|---|---|
| 프로필별 outputs (~/.hermes/profiles/*/outputs) | 기각 — 산출물 소속은 프로필이 아니라 태스크. 프로필 교체·재설치 시 산출물이 따라 감 |
| reports에 전부 통합 | 기각 — GitHub 동기화 저장소에 바이너리·대용량 영상을 섞으면 저장소가 비대해짐(실측: state-db-repair 229MB 사례) |
| outputs를 날짜 1단계만 사용 (YYYY-MM-DD/) | 기각 — 주제가 없으면 "그날 뭐 했는지"를 열어봐야 앎. YYYY-MM-DD-<주제>가 검색·Syncthing 선택 동기화에 유리 |
| inbox 대신 document_cache 연장 사용 | 기각 — 24h TTL이 구조적 데이터 소실 위험 |
| work 없이 바로 outputs에 작업 | 기각 — 미완성 파일이 열람 계층(Syncthing/웹)에 노출됨 |

---

## 8. 성공 기준 (2주 후 점검)

- outputs 밖에 새 산출물이 생기지 않음 (`/root` 직하위 find로 검증)
- 모든 outputs 하위 폴더에 README.md 존재
- kanban_complete artifacts로 채널 첨부가 기본 동작
- reports 작업 트리에 문서 외 바이너리 없음
