# 2026-08-24 일일 취합 보고 — 오케스트레이터

> 작성: 2026-08-24 22:00~22:15 KST, 작성자 default(오케스트레이터)
> 수집원: dokploy 일일보고(21:08 제출) + news 일일보고(21:04 제출) + 칸반 DB·state.db 세션 기록 교차검증
> 어제 결정된 glm-5.2 전환 후 첫 정규 취합 — 취합 크론 정상 가동 확인됨(429 재발 없음)

## ① 부문별 요약

### dokploy — doc-maker 앱 prod 전환·외부 공개 완료 (사용자 직통 세션 12:33~16:29)

**A. 배포·도메인 (변경 조작)**
- doc-maker App 재빌드 성공(12:59) — sharp 빌드 실패는 .252 VM CPU 타입(kvm64 추정, x86-64-v2 미달) 문제였고, 사용자가 Proxmox에서 host로 변경 후 해결
- 프리뷰 배포 활성화(traefik.me 기본값 + previewEnv=dev InsForge) — PR #45 더미 PR로 E2E 검증
- 외부 공개 개통: **doc-maker.vector.ai.kr** (CF 터널, E2E 200) — 첫 시도 https:true+letsencrypt가 308 루프 유발 → https:false+none 패턴으로 확정(umami 사례와 동일)
- 내부 도메인 docmaker-app.gobongs.com 제거(404 확인) — 외부 도메인만 유지
- 최종 env 구성(16:26 사용자 결정): 메인 env=**prod InsForge**(빈 DB, nip.io http), previewEnv=dev InsForge
- 당일 배포 6회·env 교체 4회

**B. 조사·검증**
- InsForge DB 상세 파악: prod=빈 DB+유저 1명(오늘 가입), dev=6테이블·견적 19건·거래처 7곳·유저 16명(실계정 포함) — dev 데이터는 무손실 보존
- Vercel/Dokploy 프리뷰 기능 비교 조사, 프리뷰 와일드카드 DNS NAT 루프백 실측(→ traefik.me 기본값 확정 근거)

**C. 장애 대응 (전부 당일 복구)**
- sharp 빌드 실패 2회(09:35, 10:50 자동배포) → CPU 타입 변경으로 해결
- 터널 308 루프 → https:false 수정
- 로그인 fetch failed → 원인은 자체 CA https URL로 env 교체(자체 유발) → http nip.io 원복
- 견적 목록 500(React #441) → 빈 prod DB 원인 → dev 바인딩 복원 후 사용자 결정으로 prod 전환 확정

### news — 정기 운영만, 이상 없음

- 트렌드 리포트 3회(08:08 조간 / 15:16 오후 / 20:07 저녁) 전부 1회 시도에 성공·전달 완료
- 주요 트렌드: 비거주 1주택 양도세 예외(당정), 제주 실종 사건 허위종결 논란→체포적부심 석방, 트럼프·김민석·장동혁·장미란 등
- zai stale_timeout 240s 조치(08-23) 이후 타임아웃 재발 없음 — 2일째 정상
- 변경 조작·실패·사용자 직통 지시 전부 없음

### 오케스트레이터(default)

- 21:00 수집 크론→일일보고 2건 생성·제출 확인, 22:00 취합 정상 실행(glm-5.2 전환 후 첫 검증 통과)
- 세션 기록 교차검증: dokploy 직통 1건·news 크론 3회 전부 일일보고에 반영 — **누락 0건**
- 당일 사용자 직통 세션(default) 없음, 칸반 당일 신규·완료 태스크는 일일보고 2건뿐

## ② 변경 조작 목록 (당일 전체)

| 부서 | 조작 |
|---|---|
| dokploy | App 재빌드 1회(총 6회 배포), 프리뷰 활성화, env 구성(4회 교체), CF DNS 와일드카드 임시전환→원복, domain.create(doc-maker.vector.ai.kr)+CF 터널 ingress 추가, domain.delete(내부 도메인) |
| news | 없음 |
| default | 없음 (취합 문서 작성 외) |

삭제·위험 조작: 내부 도메인 1건 삭제(사용자 지시, 404 확인 완료) 외 없음. 시크릿 평문 노출 0건.

## ③ 사고·이상

- **사고 등급 없음** — dokploy 장애 4건(sharp 빌드×2, 308 루프, 로그인 fetch failed, 견적 500)은 전부 당일 내 복구 완료. 이 중 2건(fetch failed, 견적 500)은 dokploy 자체 env 변경이 유발한 것으로 보고에 자진 명시 — 보고 품질 양호
- glm-5.3 429 사태(어제) 이후 전 프로필 glm-5.2로 운영 — 오늘 크론 6회(수집·취합·news 3회 포함) 전부 실패 없음
- 미해결 blocked 카드 2건(이전일자): t_3454f6b4(tailnet 패널), t_0c6ca0ed(보안 이슈 실측) — 방치 중, 정리 필요 시 지시 바람

## ④ 내일 계획

- news: 동일 크론 3종(08:08/15:16/20:07 KST) 계속 운영
- dokploy: doc-maker prod(빈 DB) 라이브 유지 — 견적 데이터 필요 시 dev→prod 선택적 이관(요청 대기). CF 잔여 A레코드(docmaker-app) 삭제, CF 토큰 최소권한 재발급은 보류 과제
- 오케스트레이터: 21:00 수집·22:00 취합 크론 계속. blocked 카드 2건 처리 여부는 사용자 결정 대기
