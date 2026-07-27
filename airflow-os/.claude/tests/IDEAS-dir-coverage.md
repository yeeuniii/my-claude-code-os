# 아이디어: conventions/ 디렉토리 주입 커버리지 (나중에 적용)

리뷰에서 나온 것. 지금 적용 안 함 — 나중에 결정 후 적용용 메모.

## 문제
서브에이전트 주입 계약에 `.claude/context/conventions/`(디렉토리)가 있는데:

1. **지시문이 문자 그대로 실행 불가** — Read 도구는 디렉토리에서 에러난다. 워커가 알아서 glob 후 개별 파일을 읽는다고 암묵적으로 가정 중.
2. **커버리지 보장 못 함** — `check-injection.sh` 의 `is_read` 가 디렉토리를 접두어 매칭으로 처리 → 하위 **아무 파일 하나만** 읽어도 PASS. `naming.md` 만 읽고 `loading.md` 를 빠뜨려도 "conventions 읽음"으로 통과.

## 해결안 (에이전트 파일은 안 건드림 — 계약은 `conventions/` 한 줄 유지)

에이전트 파일에 하위 파일을 일일이 나열하지 않는다(브리틀 + "이름으로 참조·복붙 금지" 규칙 위반). 대신 두 곳만 고친다:

### (a) 지시문을 실행 가능하게
서브에이전트 .md "먼저 Read" 섹션의
`- .claude/context/conventions/ — 이 프로젝트의 컨벤션`
→ glob-후-전부-읽기로 문구 변경. 예:
`- .claude/context/conventions/ 아래 파일 전부 — 나열(glob) 후 각각 Read`

### (b) 검증기가 디렉토리를 실제 멤버로 확장
`check-injection.sh` 의 `is_read`(현재 접두어 매칭)를 디렉토리 요건에 대해
"그 디렉토리를 실제 glob 해 현재 멤버 전부를 요구"로 바꾼다.

현재:
```python
def is_read(exp, got):
    if exp.endswith(".md"): return exp in got
    return any(g.startswith(exp.rstrip("/") + "/") for g in got)
```
바꿀 방향: 디렉토리면 `repo` 기준으로 `glob(exp + '/*.md')` 해서 각 멤버가 `got` 에 다 있는지 확인. 하나라도 빠지면 miss.
- **장점**: 에이전트 파일 편집 0. 컨벤션 파일 추가 시 자동으로 "그것도 필수"로 승격(자동 추적).
- **전제**: conventions/ 전체가 작아 "전부 읽기"가 토큰상 쌈(현재 ~130줄). 커지면 재검토.

## 열린 질문
- "전부 읽기"가 맞는 바인가, 아니면 관련 컨벤션만? 후자면 커버리지 검증은 포기(현행 유지)하고 (a)만 적용.
- builder 는 작성 대상과 무관한 컨벤션(예: 다른 팩토리 종류)까지 읽을 필요가 있나? reviewer 검증 모드는 전수 점검이 맞지만 builder 는 다를 수 있다 → 에이전트별로 요건이 갈릴 여지.
