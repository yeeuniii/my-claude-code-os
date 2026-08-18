# 재사용 (_common) — 이럴 때 이걸 써라

경로: 운영 레포의 `dags/_common/`. 공용 헬퍼는 새로 만들지 말고 먼저 여기 확인.

- **`@extract_handler`** (`decorators.py`) — **extract하는 task엔 반드시 붙인다**(`@task` 다음 줄). 결과가 비면 `AirflowSkipException`으로 자동 skip, 에러는 종류별 `AirflowException`으로 변환.
- **`cron_run_offset(cron_expr, n_days_ago, timezone="Asia/Seoul")`** (`utils.py`) — cron source 적재에서 partition_key를 "N일 전 처리날짜"로 고정할 때. `CronPartitionTimetable(..., run_offset=cron_run_offset(SCHEDULE, N_DAYS_AGO))`로 항상 함께 쓴다.
- **파티션 이벤트 발행 (네이티브)** — 한 task가 여러 파티션을, 또는 run에 없는 pk를 발행해야 할 때: `@task(outlets=[<SIGNAL>])` + `context["outlet_events"][<SIGNAL>].add_partitions(<정렬한 pk 리스트>)` 1회. pk마다 개별 이벤트로 발행된다. 발행할 파티션이 없으면 반드시 `AirflowSkipException`으로 skip한다 — 기준은 `airflow-antipatterns.md`의 'asset 트리거' 항목.
- **`emit_partitioned_asset_event(asset_uri, partition_key, extra=None)`** (`asset_event.py`) — 레거시 REST 발행. 새 DAG에 쓰지 않는다(위 네이티브 발행 사용). 미이관 사용처가 남아 있는 동안만 유지하며, 전부 이관되면 제거 검토. (`airflow_api` Connection은 이 헬퍼 외 사용처가 있으므로 제거 대상 아님.)
