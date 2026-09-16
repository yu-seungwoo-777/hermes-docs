# Slack에서 문서를 확인하는 방법 — 기능 파악 조사

- **날짜**: 2026-09-16
- **작성**: agentarch (에이전틱 코딩 설계 자문)
- **목적**: Hermes VPS가 생성한 문서/PDF/이미지 결과물을 **Slack에서 직접 확인**할 수 있는 별도 방법이 있는지 파악
- **조사 범위**: Slack 자체 문서 기능 + Hermes의 Slack 전달 경로 (공식 문서 기준)

---

## 1. 결론 요약

**존재한다.** Slack은 단순 "파일 다운로드함"이 아니라 다음 6가지 고유의 문서 확인 수단을 갖는다:

1. **인앱 미리보기** — 업로드 파일을 Slack 클라이언트에서 즉시 열람
2. **Files 브라우저** — 워크스페이스 전체 파일을 유형별(PDF/문서 등) 필터로 탐색
3. **채널 Files & links 탭** — 대화별 파일 아카이브
4. **Snippet / Slack Post** — 텍스트·문서를 Slack 네이티브 문서로 업로드 (미리보기+편집)
5. **Canvas** — Slack 자체 문서 (에이전트가 작성해 올릴 수 있음)
6. **링크 미리보기(unfurl) + 외부 링크** — VPS 쪽 URL 문서를 카드로 미리보기

Hermes 쪽에서는 deliverable mode(파일 자동 첨부) 외에 **Slack MCP 연동으로 역방향 접근(채널 검색·파일 읽기)**까지 가능하다.

---

## 2. Slack 측 기능 상세 (공식 문서 확인분)

### 2.1 인앱 미리보기 (파일 업로드 프리뷰)
- 업로드된 파일은 메시지에 **미리보기가 자동 포함**되고, 클릭하면 Slack 클라이언트 안에서 열람된다.
- **크기 제한(공식 확인)**:
  - 이미지 인라인 프리뷰: 최장변 25,000px 이하, 총 45M 픽셀 미만일 때만
  - **MS Office 파일(docx/xlsx/pptx)은 50MB 초과 시 프리뷰 없음**
  - 파일 크기 상한: **파일당 1GB** (무료/유료 공통)
- PDF는 프리뷰 가능 (filetype 목록에 `pdf` 명시, 인앱 뷰어로 열람).
- 시사점: Hermes가 생성하는 **보고서 PDF는 대부분 수 MB 수준이므로 Slack에서 바로 열람 가능**. 대용량 영상(수백 MB)은 업로드는 되지만 프리뷰 품질·편의가 떨어짐.

### 2.2 Files 브라우저 (사이드바 Files 탭)
- 사이드바 **Files**에서 워크스페이스의 모든 파일 열람 (공개 채널 + 내가 속한 비공개 채널/DM).
- **Types 드롭다운으로 파일 유형별 필터**(문서, PDF 등) — "오늘 생성된 PDF만 보기"가 가능.
- Cmd(⌘)+클릭으로 별도 창으로 열기 가능 → Mac에서 문서 확인용 창으로 상시 띄워두기 좋음.
- 파일을 **사이드바 섹션으로 조직화** 가능 (예: "Hermes 결과물" 섹션에 drag&drop).

### 2.3 채널 Files & links 탭
- 각 채널/DM 상단의 **Files & links 탭**에 그 대화에서 공유된 모든 파일이 누적됨.
- 시사점: **Hermes 전용 채널을 하나 파두면 그 채널이 곧 "결과물 피드"**가 된다. 칸반 완료 보고와 산출물이 채널별로 시간순 아카이브됨.

### 2.4 Snippet / Slack Post (네이티브 문서 형식)
- **Snippet**: 코드·텍스트를 업로드하면 **본문 일부가 잘린 미리보기 + 구문 강조 프리뷰**로 표시 (파일 오브젝트에 `preview`, `preview_highlight`, `lines`, `lines_more` 필드 존재 — API 레벨로 공식 확인). Snippet 크기 상한 1MB.
- **Slack Post**: Slack 안에서 편집 가능한 문서 형식(`mode: post`). `edit_link` 제공.
- 시사점: 마크다운 보고서를 **PDF 대신 Slack Post/snippet으로 올리면 다운로드 없이 채팅에서 즉시 읽힌다**. Hermes 쪽에서 "요약은 snippet, 원본은 PDF 첨부"로 이원화하면 확인 비용이 최소화됨.

### 2.5 Canvas
- Slack 자체 문서(Canvas). File object에 canvas 전용 속성 존재 → 프로그래밍적으로 생성 가능.
- 시사점: "프로젝트별 결과물 목차 Canvas"를 만들어두고 파일 permalink를 모아두는 인덱스로 쓸 수 있음.

### 2.6 링크 미리보기 / 외부 링크 / 검색
- **링크 공유 미리보기**: 메시지에 URL을 넣으면 콘텐츠 카드(unfurl)가 자동 표시 — VPS의 웹 파일 브라우저·문서 URL을 공유하면 Slack에서 미리보기.
- **외부 링크 생성**(유료 플랜): 파일을 Slack 밖(브라우저)에서 열 수 있는 공유 링크 발급 — 업로더만 회수 가능.
- **파일 검색**: 업로드 파일은 워크스페이스 검색 대상.
- **Slack AI**(유료 애드온): 파일 요약(`ai_summary` 필드가 API에 존재) — 문서 요약 읽기 가능. 단 별도 과금.
- ⚠️ **무료 플랜 제한**: 최근 90일 메시지·파일 이력만 보존 → 결과물 아카이브 용도로는 무료 플랜 부적합. 장기 보관은 VPS outputs + (선택) R2가 담당해야 함.

---

## 3. Hermes 측 전달·연동 경로

| 경로 | 내용 | 근거 |
|---|---|---|
| **Deliverable mode** | 에이전트가 응답에 파일 절대경로를 쓰면 게이트웨이가 Slack `files.uploadV2`로 네이티브 첨부. 문서 카테고리(pdf/docx/md/epub…), 데이터(xlsx/csv…), 프레젠테이션(pptx…) 전부 대상 | 공식 문서 확인 |
| **Kanban artifacts** | `kanban_complete(artifacts=[...])` → 완료 알림 메시지에 산출물이 함께 첨부됨. 승우님 칸반 체계와 직접 호환 | 공식 문서 확인 |
| **Slack MCP 서버** | Hermes가 Slack 워크스페이스를 **역방향으로 조회** — 채널 검색, 다른 채널 읽기. "아까 올린 그 문서 찾아줘" 같은 역검색 가능 | 공식 문서 확인 |
| `.py/.log` 제외 | 소스 코드는 자동 첨부 대상 아님 — Slack은 "사람이 보는 문서" 채널, 코드는 VS Code SSH로 역할 분리 유지 | 공식 문서 확인 |

---

## 4. Telegram과의 비교 (승우님 현재 기준 채널)

| 항목 | Telegram (현재) | Slack |
|---|---|---|
| 파일 첨부 전달 | ✅ (deliverable mode 동일 작동) | ✅ 동일 |
| 인앱 문서 미리보기 | 제한적 (PDF 뷰어는 앱 의존) | ✅ 인앱 뷰어 + Office 프리뷰(50MB까지) |
| 파일 누적 브라우징 | 대화 스크롤 / 공유 미디어 탭 | ✅ Files 탭 + 유형 필터 + 섹션 정리 |
| 네이티브 문서(Post/Canvas) | ❌ | ✅ |
| 텍스트 snippet 프리뷰 | 코드 블록으로 대체 | ✅ 전용 형식 |
| 이력 보존 | 무제한 | ⚠️ 무료 90일 / 유료 무제한 |
| 역방향 검색(MCP) | 제한적 | ✅ Slack MCP |

**판단**: Slack은 "문서 확인"이라는 목적에서 Telegram보다 확실히 우수하다(Files 브라우저, 유형 필터, Post/snippet, 인앱 뷰어). 단, **장기 보관은 어느 쪽이든 채팅 플랫폼에 맡기지 말고 VPS outputs를 원본 저장소로** 유지하는 것이 원칙.

---

## 5. 권장 구성 (이전 분석 보고서의 연장)

1. **Hermes 전용 Slack 채널** 생성 (예: `#hermes-outputs`) — 채널의 Files & links 탭이 곧 결과물 피드.
2. **칸반 완료 시 artifacts 첨부 유지** — kanban_complete(artifacts)가 Slack 완료 알림에 함께 실림.
3. **요약은 텍스트, 원본은 첨부** — 보고서는 채팅 본문에 요약 + PDF/DOCX 첨부 이원화 (AGENTS.md 규약에 추가 가능).
4. **유료 플랜 권장** — 90일 제한 때문에 무료 플랜은 아카이브 용도 부적합. 무료로 쓴다면 Slack은 "당일 확인용", 원본은 VPS outputs 단일 저장으로.
5. **역검색이 필요해지면 Slack MCP** 추가 — "지난주 보고서 찾아줘"를 Slack 안에서 해결.

---

## 6. 출처

- Slack Help — Add files to Slack (미리보기 조건, 1GB 상한, Files 브라우저, 섹션 정리, 외부 링크): https://slack.com/help/articles/201330736-Add-files-to-Slack
- Slack Developer Docs — File object (preview/lines_more, mode post/snippet, canvas/ai_summary 필드, filetype 목록): https://docs.slack.dev/reference/objects/file-object
- Slack Help — 무료 버전 제한 (90일 이력): https://slack.com/intl/ko-kr/help/articles/27204752526611
- Slack Help — 링크 공유 및 미리보기: https://slack.com/intl/ko-kr/help/articles/204399343
- Hermes 공식 문서 — Deliverable Mode: https://hermes-agent.nousresearch.com/docs/user-guide/features/deliverable-mode
- Hermes 공식 문서 — MCP (Slack 서버): https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp
