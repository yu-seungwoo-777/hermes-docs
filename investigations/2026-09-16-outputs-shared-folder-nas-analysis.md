# outputs 폴더의 공유폴더화(NAS/SMB)가 필요한가 — 확인 방법 심화 분석

- **날짜**: 2026-09-16
- **작성**: agentarch (에이전틱 코딩 설계 자문)
- **질문**: "문서를 확인하는 방법을 더 파악하고 싶다. outputs 폴더를 만들어서 NAS와 공유폴더화 해야 하나?"
- **선결 보고서**: 2026-09-16-hermes-output-delivery-analysis.md, 2026-09-16-slack-document-viewing.md

---

## 1. 결론 요약

**지금 단계에서 NAS 도입·공유폴더화는 권장하지 않습니다.**

이유는 세 가지입니다:

1. **확인 수요의 대부분은 이미 채널 첨부로 해결됨** — Hermes deliverable mode가 PDF/DOCX/이미지를 채팅에 직접 전달하므로, "파일을 찾아서 열어보는" 행위 자체가 이미 사라진 상태입니다. 공유폴더가 해결해야 할 문제가 남아 있지 않습니다.
2. **VPS와 NAS는 물리적으로 떨어져 있어 2단 동기화가 생김** — Hermes는 VPS에서 파일을 생성하고, NAS는 (있다면) 집에 있습니다. 그러면 파일 흐름이 "VPS 생성 → (동기화) → NAS → (재동기화) → Mac"이 되고, 관리 대상이 하나 더 늘어납니다. 이동 경로가 길어질수록 "어느 쪽이 최신인가" 문제가 발생합니다.
3. **SMB 공유폴더의 인터넷 노출은 구조적으로 위험** — SMB를 인터넷에 직접 노출하는 것은 전통적으로 비권장(자격증명 공격·취약점 노출 대상). 노출하려면 Tailscale 같은 VPN 레이어가 필수인데, 그 레이어를 깔 거라면 SMB 대신 더 단순한 방법(Syncthing, 웹 파일 브라우저)이 있습니다.

**올바른 질문의 방향**: "NAS를 쓸까 말까"가 아니라 "**어떤 확인 경험(Finder vs 브라우저 vs 채팅)이 필요하고, 원본 저장소는 어디로 할 것인가**"입니다.

---

## 2. "확인"이라는 행위를 3가지로 분해

문서 확인은 실제로 서로 다른 3가지 수요가 섞여 있습니다. 각각의 최적해가 다릅니다.

| 수요 | 빈도 | 최적해 | 공유폴더 필요? |
|---|---|---|---|
| **방금 나온 결과물 읽기** | 매일 | 채널 첨부 (deliverable mode) | ❌ 불필요 |
| **과거 파일 찾아보기/비교** | 주 1~2회 | 웹 파일 브라우저 (Cloudflare Tunnel 뒤) | ❌ 불필요 |
| **Mac 로컬에서 대량 파일 다루기** (영상 편집 소스 전달 등) | 가끔 | 파일 동기화(Syncthing) 또는 다운로드 | △ 이때 검토 |

공유폴더(NAS/SMB)가 유리한 조건은 이 네 가지가 **모두** 참일 때입니다:
- 파일 크기가 수백 MB~GB 단위로 잦음 (영상 원본 등)
- Mac 로컬 앱(편집기, Quick Look)에서 열어야 함
- 오프라인에서도 접근 필요
- 보관 총량이 TB 단위로 늘어남

현재까지 논의된 사용 패턴(보고서·스토리보드·프리뷰 위주)은 이 조건에 해당하지 않습니다.

---

## 3. 선택지 비교

### A. 채팅 첨부 (이미 가동 중) — 유지
- 비용 0, 파일 찾기 불필요. Slack을 쓴다면 Files 탭+유형 필터로 과거 파일 브라우징까지 가능.
- 한계: 원본이 채팅 플랫폼 사본이라는 점. **원본 저장소는 어디든 별도로 있어야 함** — 이것이 outputs 폴더의 본래 역할.

### B. 웹 파일 브라우저 (filebrowser 등) + Cloudflare Tunnel — 1순위 추가 후보
- outputs 디렉터리만 마운트해 `files.example.com`으로 노출. PDF/이미지/영상 뷰어 내장, 인증 필요.
- 이미 보유한 터널 인프라로 추가 비용 없음. 이전 보고서에서 지적한 "별도 웹 브라우저 구현"이 바로 이것.
- 전제: Cloudflare Access 또는 강한 인증, outputs만 노출.

### C. Syncthing (VPS ↔ Mac 직접 동기화) — Finder 경험이 필요해질 때
- outputs 폴더를 Mac의 로컬 폴더로 **실시간 단방향 수신**. Hermes가 파일을 쓰면 Mac Finder 폴더에 그대로 나타남.
- NAS·SMB·포트 노출 없이 "공유폴더 경험"을 얻는 가장 단순한 방법. 인터넷을 통한 P2P 동기화(암호화됨), 서버 포트를 외부에 열지 않음.
- 커뮤니티 검증 조합: Syncthing(동기화) + FileBrowser(모바일/웹 열람) — 역할이 명확히 분리됨.

### D. SMB 공유폴더 (VPS를 직접 마운트) — 비권장
- Finder에서 네트워크 드라이브로 보이는 장점은 있으나:
  - **인터넷 직접 노출은 원칙적 금지 수준** (자격증명 브루트포스·프로토콜 취약점의 상시 표적). VPN(Tailscale) 필수.
  - macOS SMB는 **성능·연결 안정성 문제로 악명이 높음** — Finder 네트워크 복사 속도 불안정, Tailscale 환경에서의 마운트 유지 문제 사례 다수, 튜닝을 위해 nsmb.conf 수동 수정이 필요한 수준.
  - Finder가 네트워크 볼륨의 .DS_Store·메타데이터를 쓰면서 에이전트 작업 디렉터리가 오염될 수 있음.
- 결론: 같은 노력을 C(Syncthing)나 B(웹 브라우저)에 쓰는 것이 낫습니다.

### E. NAS 도입 — 아직 아님, 트리거 조건만 정의
- NAS는 "저장 용량·백업·홈랩 서비스"의 문제지, "문서 확인"의 문제가 아닙니다. 문서 확인만 보면 NAS를 사도 위 B/C가 필요합니다 (NAS의 SMB는 집 네트워크 안에서나 편리).
- VPS(Hermes) → NAS 흐름을 만들면 2단 동기화가 생겨 관리 복잡도가 오히려 증가.
- **도입 트리거 (이 중 2개 이상 충족 시 재검토)**:
  1. 영상 원본 등 GB 단위 파일이 주 3회 이상 오가고, Mac 로컬 편집이 필수
  2. 보관 총량이 VPS 디스크 예산을 압박 (수백 GB~TB)
  3. 집에서 운영하는 백업/아카이브 체계를 원함
  4. 가족·팀과 파일을 공유할 필요

---

## 4. 권장 구성 (단계별)

```
[Stage 1 — 지금, 추가 인프라 0]
VPS ~/workspace/outputs/YYYY-MM-DD-<주제>/   ← 원본 단일 저장소 (single source of truth)
  ├─ 채널 첨부로 "방금 나온 것" 확인 (이미 작동)
  └─ AGENTS.md에 outputs 규약 명문화

[Stage 2 — 과거 파일 브라우징이 불편해지면]
+ 웹 파일 브라우저 (outputs만 마운트)
+ Cloudflare Access 인증
→ files.example.com

[Stage 3 — Mac 로컬 파일 경험이 필요해지면]
+ Syncthing: VPS outputs → Mac 수신 폴더 (단방향)
→ Finder에서 로컬 폴더처럼 열람, NAS 불필요

[NAS는 Stage 3 이후에도 용량·백업 문제가 남을 때 별도 판단]
```

핵심 원칙: **원본은 항상 VPS outputs 하나로.** 채널 첨부는 사본, Mac 로컬도 사본, (미래) NAS도 사본. 사본들은 언제든 다시 만들 수 있으므로 시스템이 단순합니다. 원본이 두 곳에 생기는 순간(예: NAS를 원본으로 쓰면서 Hermes가 거기에 직접 쓰는 구조) 동기화·충돌 관리 비용이 커집니다.

---

## 5. 자주 나오는 반론에 대한 답변

- **"Finder에서 보는 게 제일 편하지 않나?"** — 맞습니다. 하지만 그 수요는 Stage 3(Syncthing)으로 해결되고, SMB 서버 운영은 필요 없습니다. Syncthing은 일반 폴더라서 Quick Look, Spotlight 검색 등 Finder의 모든 이점을 그대로 누립니다.
- **"NAS를 사두면 나중에 편하지 않나?"** — 저장소는 문제가 생겼을 때 사도 늦지 않습니다. 반대로 지금 사면 "VPS→NAS 동기화 파이프라인"이라는 새 관리 대상이 먼저 생깁니다.
- **"공유폴더면 에이전트가 직접 쓰니까 실시간이잖아"** — VPS의 로컬 폴더도 동일합니다. Hermes는 자기 파일시스템에 쓰는 것이고, 공유폴더화는 그걸 **보는 방법**의 문제일 뿐입니다.

---

## 6. 결론

- outputs 폴더 자체는 **지금 만들어야 맞습니다** (원본 저장소 + AGENTS.md 규약).
- 그러나 "NAS와 공유폴더화"는 **하지 않습니다.** 필요 경험은 ① 채널 첨부(이미 있음) → ② 웹 브라우저(필요시) → ③ Syncthing(필요시) 순으로, 전부 NAS·SMB 없이 구현됩니다.
- NAS 재검토 트리거: GB급 영상 파일의 잦은 로컬 편집 + TB급 보관 수요가 동시에 생길 때.

---

## 7. 출처

- SMB 인터넷 노출 비권장 (Super User): https://superuser.com/questions/311658/make-a-network-drive-available-over-the-internet
- macOS Finder 네트워크 파일 복사 성능 문제 (Jeff Geerling, 2024): https://www.jeffgeerling.com/blog/2024/macos-finder-still-bad-network-file-copies
- macOS SMB 성능 튜닝 필요 사례 (nsmb.conf 수동 수정): https://gist.github.com/othyn/4554c1f409f34d1674ba2095acf441ee
- Tailscale 환경 macOS SMB 연결 문제 사례 (Reddit r/Tailscale): https://www.reddit.com/r/Tailscale/comments/1oj5hc5/
- Syncthing + FileBrowser 조합 사례 (Hacker News): https://news.ycombinator.com/item?id=40264170
- Hermes deliverable mode (공식): https://hermes-agent.nousresearch.com/docs/user-guide/features/deliverable-mode
