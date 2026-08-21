# 네이밍

## dag_id
- `<db엔진>_<스키마>_<테이블>` — 최종 적재 대상 기준. 예: `doris_game_silver_session`.
- 한 DAG가 여러 대상을 처리하면 테이블 자리에 그걸 아우르는 공통 이름을 쓴다.
- `idb`는 회사 MariaDB의 별칭 → MariaDB로 적재하면 `idb_` 접두.
- `vpn_`·`alert_`는 예외: 데이터 ETL이 아니라 크론잡류.
- `_dag` 접미는 붙이지 않는다.

## task_id
- 동사 스네이크. 공통 단계는 표준 이름을 재사용: `initialize_date`, `extract`, `transform`, `load`, `emit_outlets`.
- `emit_outlets`는 **발행 전용 task**(데이터 작업 없이 fan-in 지점에서 asset 신호만 발행)의 이름이다. 적재 task가 outlets를 함께 선언하는 경우(적재 성공 = asset 갱신 신호, 또는 OM 계보용 outlet)는 별도 발행 task를 만들지 않고 `load*` 이름을 유지한다.

## 함수·변수
- 헬퍼 함수는 **동사로 시작**한다 (`_build_...`, `_parse_...`, `_validate_...`) — 무엇을 하는지 이름만으로 드러나게.
- 용어 통일은 `.claude/context/terms.md`를 따른다 — 코드 식별자(컬럼·필드·변수)와 주석, 도메인 개념(예: 분류 라벨)에도 적용한다.

## 파일명
- 1파일 = 1 DAG면 파일명 = dag_id. 팩토리(`airbyte_el`, `dbt_transformation`)는 1파일 = N DAG.

## 동적 식별자 sanitize
- 동적 id는 `[^A-Za-z0-9_.-]` → `_` 치환(`dbt_lib/utils.py`의 `safe()`). appid의 `.`은 `-`로.

## Connection
- conn_id: 스네이크. 대체로 `_conn` 접미(`doris_conn`, `idb_conn`), 예외 있음(`airflow_api`, `sftp`).
- Variable dict/list 값은 `Variable.get(key, deserialize_json=True, default=...)` — `airflow.sdk.Variable` 기준. `default_var`는 Airflow 2 시그니처라 sdk에서 TypeError.
