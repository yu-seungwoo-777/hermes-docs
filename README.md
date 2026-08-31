# hermes-docs — Hermes 부대 문서·산출물 공용 저장소

서버 `/root/reports/`와 직결된 프라이빗 문서 공간. 생성된 보고서·설계 산출물·사고 기록을
GitHub에서 열람·추적하기 위한 단일 저장소다.

## 구조

```
/root/reports/  ← 이 저장소의 로컬 워킹 트리
├── daily/        일일 보고 (YYYY-MM-DD-<프로필>.md, UTF-8 with BOM)
├── security/     보안 관련 기록
├── designs/      설계 문서 (아키텍처·워크플로우 스펙)
├── incidents/    장애·사고 기록
└── README.md     이 파일
```

## 커밋 규칙 (전 프로필 공통)

1. **커밋 컨벤션**: `[<프로필명>] <내용>` — 예: `[dokploy] 08-31 일일보고 추가`
2. **푸시 절차**: `git pull --rebase` → add/commit → `git push` (문서 리포라 충돌 거의 없음)
3. **인코딩**: 사용자가 열람하는 .md는 **UTF-8 with BOM** 유지
4. **보안**: 시크릿·토큰·API 키 평문 절대 금지
5. **불변 원칙**: 다른 프로필이 작성한 보고서를 임의 수정하지 않는다 (오탈자 등 예외는 커밋 메시지에 명시)

## 접근

- 모든 Hermes 프로필(default·dokploy·news·biseo-jaeyoung·agentarch)이 서버 파일시스템을 통해
  동일하게 읽기/쓰기 가능하다. GitHub 쪽 권한은 저장소 소유자(yu-seungwoo-777)가 관리한다.
- 리모트: `origin = https://github.com/yu-seungwoo-777/hermes-docs.git` (PRIVATE)
