# Syncthing 단방향 동기화(VPS outputs → Mac/iPhone) 브리핑

- **날짜**: 2026-09-16
- **작성**: agentarch (에이전틱 코딩 설계 자문)
- **질문**: "Syncthing: VPS outputs → Mac 수신 폴더 (단방향)"에 대한 상세 브리핑. Mac, iPhone 등에서 사용 가능한지?
- **선결 보고서**: 2026-09-16-outputs-shared-folder-nas-analysis.md

---

## 1. 한 줄 요약

**Mac은 공식 앱으로 완전 지원, iPhone은 서드파티 앱(Synctrain)으로 지원됩니다.** 둘 다 무료이며, iPhone 쪽은 iOS의 백그라운드 제약만 이해하면 실용적으로 쓸 수 있습니다.

---

## 2. 단방향 구조의 공식 보장 (Syncthing 공식 문서 확인)

Syncthing은 폴더 유형으로 단방향을 **공식 기능**으로 제공합니다:

- **VPS 측: "Send Only" 폴더** — 참조 원본(reference copy)용으로 문서에 명시된 용도. 다른 기기의 변경을 모두 무시. Mac에서 실수로 뭔가 바꿔도 VPS 원본은 건드리지 않음. 상대가 변경하면 "Override Changes" 버튼으로 VPS 상태를 강제할 수도 있음.
- **Mac/iPhone 측: "Receive Only" 폴더** — 클러스터의 변경은 모두 적용하되, **로컬 변경은 절대 다른 기기로 전송되지 않음**. 백업 사본·복제 미러용으로 문서에 명시된 용도. 로컬에서 실수로 수정·삭제하면 "Revert Local Changes"로 원상 복구 가능.

즉 "단방향"이 약속이 아니라 **프로토콜 레벨에서 강제**됩니다. 이중 잠금(Send Only + Receive Only)이므로 한쪽을 잘못 설정해도 역방향 오염이 없습니다.

### 통신 방식 (포트·보안)
- 기기 간 **TLS로 암호화**, 장치 ID(지문) 상호 승인 방식 — ID를 서로 등록하지 않으면 연결 자체가 안 됨.
- **포트를 인터넷에 열 필요 없음**: 글로벌 디스커버리 + 릴레이 서버를 기본 사용. 둘 다 직접 연결이 안 될 때 릴레이를 통해 우회하며, 이때도 **릴레이 서버는 암호화된 트래픽만 중계**(내용 열람 불가).
- Tailscale과 병용 가능(직접 연결 확률↑)이지만 필수 아님.

---

## 3. 기기별 지원 현황

### Mac — ✅ 공식 지원 (문제없음)
- **공식 macOS 앱** 존재(메뉴바 상주, `brew install syncthing` 또는 공식 dmg). Syncthing 코어가 macOS를 공식 지원 플랫폼으로 유지.
- 구성: 수신 폴더를 `~/HermesOutputs` 같은 로컬 폴더로 지정 → Finder 일반 폴더처럼 작동. **Quick Look(스페이스바 미리보기), Spotlight 검색, 미리보기 앱 전부 그대로 사용 가능.**
- 서드파티 앱 **Synctrain도 macOS를 지원**(iOS·macOS 범용) — 선택지가 하나 더 있음.

### iPhone — ✅ 가능, 단 조건 이해 필요
공식 Syncthing 앱은 없으며 **서드파티 2개**가 실질 선택지:

| 앱 | 가격 | 상태 | 특징 |
|---|---|---|---|
| **Synctrain** (추천) | 무료, 오픈소스(MPL-2.0) | **활발** (2026-09 커밋, Syncthing 2.0.9 코어 탑재, iOS 26 대응) | 선택적 동기화(폴더 일부만 수신), **온디맨드 접근**(로컬에 없는 파일을 피어에서 스트리밍/다운로드 — VPN 불필요), 원격 썸네일, Shortcuts 연동, Files 앱 연동 |
| Möbius Sync | 유료(~$10) | 유지보수 느림 | 초기 iOS Syncthing 앱. Synctrain 등장 후 선택 이유 약화 |

**iOS의 구조적 제약 (공식 문서로 확인된 부분)**:
- iOS는 앱에게 상시 백그라운드 실행을 허용하지 않음 → 실측 보고 기준 **충전 중 약 시간당 1회, 배터리 모드로는 시간당 몇 분** 수준으로만 백그라운드 동기화.
- **운용 방침**: iPhone은 "새 문서 푸시 수신함"이 아니라 **"필요할 때 열어서 확인하는 뷰어"**로 쓰는 게 맞음. Synctrain의 온디맨드 접근(VPS에서 그때그때 가져오기/스트리밍)이 이 패턴에 정확히 맞음.
- 당일 산출물 확인은 어차피 채널 첨부(Telegram/Slack)가 1차 경로이므로, iPhone Syncthing은 **과거 파일 열람 보조 수단**의 위치.

### (참고) Android
- 공식 Android 앱은 2024년 말 개발 종료(EOL). 커뮤니티 포크 **syncthing-fork**가 사실상 표준. 백그라운드 동기화는 iOS보다 자유로움.

---

## 4. 구성 절차 (권장안)

```
[VPS]
1. syncthing 설치 (패키지 매니저)
2. 폴더 추가: ~/workspace/outputs → 폴더 유형 "Send Only"
3. Mac·iPhone 장치 ID 승인

[Mac]
1. 공식 앱 설치 (brew install syncthing 또는 dmg)
2. 폴더 수락 시 유형 "Receive Only" 확인
3. (권장) 버저닝: "휴지통 버저닝" 활성화 — VPS에서 삭제된 파일도
   Mac의 .stversions에 보존됨

[iPhone]
1. Synctrain 설치 → 같은 폴더 선택적 수신 (또는 온디맨드)
```

### 반드시 알아야 할 동작 2가지

1. **삭제도 동기화됩니다** — Sync는 복제이지 백업이 아님. Hermes가 outputs에서 오래된 파일을 정리하면 Mac·iPhone에서도 사라집니다. 대응:
   - 수신 측에 **휴지통 버저닝(Trash-can file versioning)** 켜기 → 삭제 파일이 `.stversions`에 보존
   - 또는 Hermes의 outputs 정리 규약 자체를 "삭제 대신 archive/ 이동"으로 (이전 보고서의 archive/ 개념과 연결)
2. **Mac에서 파일을 지우면 "Revert Local Changes"가 떠요** — Receive Only이므로 데이터 손상은 없고, 버튼 하나로 VPS 기준 상태로 복구됩니다. 이것이 의도된 설계.

---

## 5. 이 구조가 맞는지 최종 판정

| 항목 | 평가 |
|---|---|
| Mac에서 Finder 기반 문서 열람 | ✅ 최적. Quick Look·Spotlight 포함 |
| iPhone 열람 | ✅ 가능 (Synctrain). 단 실시간 푸시 기대 금지 — 온디맨드 뷰어로 활용 |
| 보안 | ✅ TLS + 장치 ID 승인 + 포트 미개방. SMB 노출 대비 구조적으로 안전 |
| 단방향 보장 | ✅ Send Only + Receive Only 이중 잠금 (공식 기능) |
| 유일한 주의점 | 삭제 전파 — 휴지통 버저닝 또는 archive 이동 규약으로 해결 |
| 원본 위치 | 여전히 VPS outputs 단일 원본 원칙 유지 (Mac/iPhone은 전부 사본) |

**권장 순서 변화 없음**: 당일 확인은 채널 첨부 → 과거 파일 브라우징은 웹 브라우저 → Finder/오프라인 경험 필요시 Syncthing. Syncthing은 Stage 3이지만, 도입을 결정하면 **Mac(공식 앱)부터** 시작하고 iPhone은 Synctrain으로 보조하는 것이 안정적인 순서입니다.

---

## 6. 출처

- Syncthing 공식 문서 — Folder Types (Send Only / Receive Only 동작·복구 버튼 명세): https://docs.syncthing.net/users/foldertypes.html
- Synctrain (sushitrain) 저장소 — iOS/macOS 지원, 온디맨드 접근, 선택적 동기화, 2026-09 활동 내역: https://github.com/pixelspark/sushitrain
- Synctrain App Store — Syncthing 2.0.9 코어, iOS 26 대응: https://apps.apple.com/us/app/synctrain/id6553985316
- iOS 백그라운드 동기화 실측 (~시간당 1회, 충전 중): https://www.reddit.com/r/selfhosted/comments/1ke2wsv/
- Syncthing 포럼 — iOS/iPadOS용 Synctrain 안내: https://forum.syncthing.net/t/syncthing-on-ios-ipados/24610
- 릴레이·보안 모델: https://docs.syncthing.net/users/security.html
