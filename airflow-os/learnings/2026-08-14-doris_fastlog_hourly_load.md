---
type: task
date: 2026-08-14
subject: fastlog load asset 발행 REST 우회 → Airflow 3.3 네이티브 add_partitions 전환 (이슈 #33)
dag_id: doris_fastlog_hourly_load
---

## 무엇을
리팩터. `emit_ready_event`의 asset 이벤트 발행을 REST 우회(`_common/asset_event.py`의 `POST /api/v2/assets/events`)에서 3.3 네이티브 `outlets=` + `outlet_events[...].add_partitions([...])`로 교체. `group_by_logdate` + `.expand` 매핑을 없애고 단일 task로 축소, extra 미탑재. 커밋 `b2442ec` (브랜치 2613.0.0).

## 왜 (결정과 트레이드오프)
- **단일 task 축소 (expand 유지 대신)**: 매핑 폭이 최대 2(KST-PST 날짜 경계)라 개별 재시도·UI 가시성 실익이 미미했고, 매핑 구조에선 부분 재시도·clear 시 일부 logdate가 중복 발행되는 결함이 있었다. 단일 task + 성공 시점 발행은 "성공 1회당 발행 1회". 대가는 `group_by_logdate` task 실행 이력이 UI에서 끊기는 것(사용자 승인).
- **extra 제거 (공유 extra 유지 대신)**: 네이티브 경로는 per-partition extra가 없고(`accessor.extra`가 전 파티션 공유) 다운스트림 dbt가 extra를 안 읽어서 뗐다.
- **asset_event.py 존치 (이슈 초안은 제거)**: grep 결과 `airbyte_el`·`doris_prediction_report_prevenue_v202411`도 사용 중, `airflow_api` Connection은 `alert_failed_dag`·`dbt_lib/factory`도 사용. 이 DAG의 import만 제거했다.

## 발견 / 배운 점
- **이슈에 적힌 설계 초안도 grep으로 재검증해야 한다.** "유일 사용처" 전제가 이슈 작성 시점(7월) 이후 새 사용처(airbyte_el 등)가 생겨 뒤집혔다. 파일 삭제 항목은 구현 직전 사용처 grep이 필수.
- **linchpin을 staging 실행 전에 소스 검증으로 해소할 수 있었다.** lab venv가 운영과 동일 3.3.0이라 `task_runner.py`(`_serialize_outlet_events`)·`taskinstance.py`(`_register_asset_changes`)·`assets/manager.py`를 직접 읽어 확인: add_partitions는 producer schedule 종류와 무관하게 동작, partition_key마다 개별 이벤트, REST가 쓰던 `register_asset_change`와 동일 진입점, producing run의 partition_key를 쓰지도 오염시키지도 않음.
- **outlets 선언 task는 발행 없이 성공하면 평면(무파티션) 이벤트가 나간다.** `partition_keys`가 비었을 때의 fallback 경로. 빈 입력이면 반드시 skip으로 빠져야 동작이 보존된다 — 기존 매핑 구조에선 "인스턴스 0개"가 이 역할을 공짜로 해줬는데, 단일 task 전환 시 명시적 skip이 필요해진 것.
- `partition_keys`가 있으면 평면 이벤트는 발행되지 않는다(중복 걱정 불필요). 이벤트는 "1건에 키 여러 개"가 아니라 **키별로 쪼개져** 발행된다.
- 재처리 목적으로 emit task를 clear하는 운용은 다운스트림 dbt의 `skip_if_already_processed` 게이트 때문에 no-op일 수 있다. 재처리는 dbt run을 직접 clear/trigger.

## 다음에 재사용할 것
- **REST 우회 이관 후속 후보 2건**: `airbyte_el`, `doris_prediction_report_prevenue_v202411`. 전부 이관돼야 `_common/asset_event.py` 제거 논의 가능(별도 이슈 권장).
- **네이티브 partition 발행 패턴**: `@task(outlets=[SIGNAL])` + `context["outlet_events"][SIGNAL].add_partitions(sorted_keys)` 1회 + 발행할 게 없으면 `AirflowSkipException`. 이 세 요소가 한 세트다(skip 없으면 평면 이벤트 유출).
- **버전 의존 기능 검증 순서**: 운영 `/api/v2/version` 확인 → lab venv를 같은 버전으로 → task-sdk·server 소스를 직접 읽어 전제 검증 → 그 다음 구현. 문서 예시(PartitionedAtRuntime)가 요구 조건처럼 보여도 소스가 정답.
- 리뷰어 NIT: task 파라미터명 `params`는 Airflow context 예약 키와 겹친다 — 다음 리팩터 때 개명 후보.
