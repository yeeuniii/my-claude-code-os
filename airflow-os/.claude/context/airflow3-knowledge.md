# Airflow 3 지식 (버전 종속 · 닳음 주의)

> Airflow 3.x 기준. 버전 올릴 때 이 파일을 갱신한다.

## 진입점 · import 경로
- TaskFlow·Asset 등 진입점은 `airflow.sdk`에서: `from airflow.sdk import dag, task, Asset, ...`.
- 대체된 import(구 → 신):
	- `airflow.operators.python` → `airflow.providers.standard.operators.python` (`PythonOperator`)
	- `airflow.operators.empty` → `airflow.providers.standard.operators.empty` (`EmptyOperator`)
	- `airflow.models.dagbag` → `airflow.dag_processing` (`DagBag`)
	- `airflow.datasets` → `airflow.sdk` (`Asset`)
	- XCom base: `from airflow.sdk.bases.xcom import BaseXCom`
- context 키·이벤트 변경: `execution_date` → `logical_date`, `triggering_dataset_events` → `triggering_asset_events`.

## cron 발사 모델 (v2와 다름)
- cron 문자열을 `schedule`에 주면 어떤 timetable이 되는지는 `scheduler.create_cron_data_intervals`가 정한다. **기본값 `False`**(v3 기본, 3.3.0에서 확인):
	- `False` → `CronTriggerTimetable`. **`logical_date` = 트리거 시각**이고 data_interval은 폭이 0이다(start == end == 트리거 시각). v2의 interval lag 없음.
	- `True` → `CronDataIntervalTimetable`(v2 방식). `logical_date` = data_interval 시작 = **직전 발사 시각**.
- 그래서 `logical_date`로 대상 날짜를 정하는 DAG는, **하루가 온전히 지난 날짜**를 잡으려면 하루를 빼야 한다. 오늘 08:30에 뜬 run의 `logical_date`는 오늘 08:30이라, 보정 없이 쓰면 그날 08:30까지분만 수집한다. ETL은 1시간, dbt는 n_days_ago만큼 수동 보정한다.
- **테스트 함정**: `AIRFLOW__CORE__UNIT_TEST_MODE=true`를 켜면 `unit_tests.cfg`가 이 설정을 `True`로 뒤집어 timetable이 운영과 달라진다. 스케줄·날짜 시맨틱을 검증하는 테스트에서는 켜지 않는다.

## 워커 · 메타DB
- 워커는 메타DB 직접 조회 불가 → REST `/api/v2` 사용. `POST /auth/token`(Simple Auth Manager JWT) → Bearer. datetime 필터는 `_gte`/`_lte`만(반열림은 1μs 빼서).
- `RuntimeTaskInstance`에 `get_dagrun()` 없음 → 필요한 집계는 XCom 등으로 우회.
