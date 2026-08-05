# 멱등 적재 · 날짜 결정

## 전송 수단 (destination에 밀어 넣는 물리적 방식)

볼륨(런당 행수)이 근거다. 설계도에 수단과 근거를 함께 적는다.

- **stream load** (HTTP `_stream_load`): 런당 수천 행 이상. Doris 표준 벌크 적재.
- **executemany insert** (`MySqlHook.insert_rows`, 파라미터 바인딩): 런당 수백 행 이하. stream load가 오버킬인 소량 upsert.
- **INSERT INTO SELECT / dbt**: 데이터가 이미 Doris 안에 있는 테이블 간 변환.

## 적재 방식 (멱등)
- **upsert**: PK/UNIQUE KEY로 덮어쓰기. (Doris는 PK 테이블 stream load가 곧 upsert, MariaDB는 `insert_duplicatekey_update` = ON DUPLICATE KEY)
- **delete-then-insert**: 대상 날짜/파티션을 지우고 다시(파티션 삭제 전 파일 존재 확인 = fail-open).
- **snapshot**: 오늘 현재 상태를 `snapshot_date`로 upsert(logical_date 아님).
- **지양**: append-only(멱등 아님), truncate-and-load(전량 교체라 위험 — 꼭 필요할 때만).

## 날짜 결정 (initialize_date, EL 적재 표준)
- "이번 run이 며칠자 데이터인지" 정해 다음 task들에 넘긴다.
- 우선순위:
	1. conf (수동/백필)
	2. partition_key (asset/cron)
	3. data_interval_start 에서 n_days_ago 차감
	4. today
- 정한 날짜 문자열을 `return`(XCom)해서 다음 task들이 받아 쓴다.
