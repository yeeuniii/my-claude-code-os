---
type: task
date: 2026-08-07
subject: store_reviews LLM enrich DAG — helpshift v3 틀 복제 사이클
dag_id: doris_cx_silver_store_reviews_llm
---

## 무엇을
helpshift_issues_llm v3(단일 호출) 틀을 복제해 스토어 리뷰 enrich DAG 신규 작성. interview→구현→테스트(41/41)→리뷰→승인→커밋(`feature/cx-llm`)·MR !43(→2612.3.0). 산출물은 번역(제목·본문 별도 컬럼)+분류(단일 레벨 7라벨), 요약 없음.

## 왜 (결정과 트레이드오프)
- **커서 시각축을 `loaded_at` 대신 `date`로**: 실측 결과 silver가 dbt 풀 리로드라 전 9,378행의 `loaded_at`이 동일 — 커서로 쓸 수 없었다. `date`(android=갱신일)는 DATE 단위라 같은 날 수정 재분류를 못 잡는 대가를 감수.
- **라벨은 새로 묻지 않고 SSOT 승계**: 인터뷰에서 taxonomy를 물었더니 사용자가 이미 확정 문서(`docs/llm_migration.md` §8.1·8.2, 프롬프트 v4, 모델 v4-flash+CoreWeave)를 답으로 줬다. CX 협의까지 끝난 결정이었다.
- **LLM 입력에서 platform 제거** (리뷰 WARN 수용): eval/gold set이 검증한 입력 분포(rating+제목+본문)에 없는 필드 — 검증 안 된 입력 분포를 프로드에 넣지 않는다.
- **기준일 Variable 공유**(`cx_llm_start_date`): 전용 변수 대신 CX LLM 정책값 한 곳 관리.

## 발견 / 배운 점
- **운영 레포 `docs/`에 확정 결정이 산다.** 조사 때 dags·designs만 보고 docs/를 안 훑어 taxonomy를 객관식으로 새로 물을 뻔했다 — 사용자 답변으로 SSOT를 뒤늦게 발견.
- **sql-executor의 `airflow` DB는 레거시 Airflow 2 메타DB다.** 운영 Airflow 3은 `airflow3`(REST API가 정확) — asset·DAG 등록 확인을 레거시 DB에서 하면 "없다"로 오판한다. 실제로 한 번 헛다리 짚었다.
- lab SKILL.md의 `t.unmap(None)` 스니펫은 decorated mapped operator에서 동작 안 함(테스터 실측) — 해석된 kwargs를 넘겨야 한다. SKILL.md 갱신 후보.
- 서브에이전트가 API 오류로 2회 중단됐지만 SendMessage 재개로 진행분(파싱·구조 검증)을 잃지 않고 이어갔다.
- 커밋 시점에 다른 세션의 레포 정리(`docs`·`designs`·`sandbox` gitignore화, scripts→sandbox 이동)와 겹쳤다 — 커밋 전 `git status` 전수 확인이 이런 드리프트를 잡았다.

## 다음에 재사용할 것
- **`*_llm` enrich 복제 패턴**: v3 뼈대(커서 자가 치유·map_indexes 자리보존·leaf 3분기)는 그대로 두고, 설계도에는 바뀌는 축만 명시하면 된다 — 산출물 스키마 · 커서 시각축 · 라벨 구조(계층/평면) · 입력 조립. 이번에 워커가 이 방식으로 복제 실수 0건.
- **커서 시각축은 반드시 실측**: 후보 컬럼의 값 분포(`GROUP BY loaded_at` 한 방)로 풀 리로드 여부부터 확인.
- **LLM 입력 필드는 eval이 재본 분포와 일치시킨다** — 편해 보여서 필드를 추가하면 검증 밖 입력이 된다.
- 라벨·모델·프롬프트류 확정 사항은 사용자에게 근거 문서가 있는지 먼저 묻는다 — 이 사이클에선 작업 노트에 있었지만, 그 위치는 SSOT가 아니며 옮겨 다닌다(2026-08-11 사용자 확인).
