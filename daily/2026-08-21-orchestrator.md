# 2026-08-21 일일 취합 보고 — orchestrator (대장)

> 작성: 2026-08-22 소급 작성 (칸반·세션 기록 기반 복원 — 보고 문서 제도 시행 전날분)

## 부문별 요약 (dokploy)

- **배포**: InsForge doc-maker prod/dev 2벌 신규 배포, 헬스 200 (v2.3.1) — 상세는 [2026-08-21-dokploy.md](2026-08-21-dokploy.md) 참조
- **인프라**: Mac Studio ↔ Hermes 양방향 SSH (MAC-STUDIO alias), Mac 측 .env.local 시크릿 주입 (600)
- **지식**: 운영 함정 4종 스킬 반영 (composeType 제약, accessToken/tableName 필드, PostgREST 캐시 404, API 키 정책)
- **조사**: 칸반 끝단 테스트 1건 (읽기 전용, 프로젝트 3개 정상)

## 대장 직접 작업

- **glm-5.3 컨텍스트 윈도우 수정 (default 프로필)**: models.dev 캐시에 zai/glm-5.3 미등록 → 202,752 폴백 문제. `model_overrides`로 context_window 1,000,000 / max_output_tokens 131,072 오버라이드 완료. 함정 발견: 점 포함 모델 ID는 `hermes config set` dotted-path로 못 씀 — save_config() 직접 기록 필요.

## 검증 내역

- t_7ef44f3f (dokploy 보고): prod/dev 헬스 200 + Mac .env.local 키로 API 인증 200 실측, 시크릿 2종 권한 600 확인, SSH 양방향 동작 확인, 운영 지식 스킬 반영 확인 — **전량 사실로 확정**

## 사고·이상

- **워커 보고 후 사용자 미전달**: 위 검증 완료(18:17) 후 사용자에게 알리지 않아 사용자가 직접 워커에게 물어야 알았음. 원인: 보고 태스크가 워커 세션에서 생성되어 알림 구독 부재 + 대장의 전달 소홀. → 8/22 보고 체계 신설(즉시 하위→대장 보고 / 21:00 전원 일일 보고 / 22:00 대장 취합)로 재발 방지

## 진행 중 / 보류

- Dokploy 삭제 보호 부재 → 백업/감시 cron 제안 (사용자 승인 대기)
- dokploy 프로필 glm-5.3 컨텍스트 오버라이드 미적용 상태였음 → 8/22 오전 해결 완료

## 내일(8/22) 계획 (당시 기준)

- 보고 체계 가동: 21:00 전원 일일 보고 / 22:00 대장 취합 (첫 실행)
