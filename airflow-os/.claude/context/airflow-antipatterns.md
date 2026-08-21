# Airflow 안티패턴

## top-level 코드
❌ 최상단에서 무거운 연산·DB 연결·API 호출 (스케줄러가 파싱마다 실행)
✅ 실제 작업은 task 함수/Operator 안에서

## Variable·Connection 파싱 시점 접근
❌ top-level에서 `Variable.get()`·Connection 조회 (파싱마다 메타DB 히트)
✅ 템플릿 필드에 `{{ var.value.x }}` Jinja, 또는 task 함수 안에서 조회

## 멱등성
❌ append-only 적재 (재실행·백필·retry 시 중복)
✅ 키 upsert 또는 파티션 delete-then-insert

## 실행시각 하드코딩
❌ `datetime.now()`·오늘 날짜를 코드에 박기 (백필이 깨짐)
✅ `logical_date` / `data_interval` / `ds` 사용

## catchup
❌ `start_date` 과거 + `catchup=True` (배포 순간 대량 run)
✅ 기본 `catchup=False`, 과거는 수동 backfill로 범위 통제

## XCom 대용량 전달
❌ records(list/dict — 메타DB JSON 직행)로 수 MB+ 데이터 전달 (메타DB 부하)
✅ 외부 스토리지(S3/파일/테이블)에 두고 XCom엔 포인터(경로·키)만 — DataFrame XCom은 백엔드가 이걸 자동으로 한다(`platform.md`). 수단 선택 기준은 `conventions/loading.md`

## 안정성 설정
❌ `retries`·`execution_timeout` 없음, 광범위한 `depends_on_past`
✅ `default_args`에 `retries`·`retry_delay`·`execution_timeout` (기본 3 / 5m / 30m)

## leaf 태스크가 실패를 삼킴
❌ 유일한 leaf에 `trigger_rule=all_done`만 걸어두기 — DagRun 상태는 leaf로 정해지므로 상류 실패·전량 실패가 success로 끝난다
✅ leaf가 "처리 대상이 있었는데 결과 0건" 같은 판정을 스스로 해서 실패시킨다

## 매핑 결과를 위치로 잇기
❌ 매핑 태스크 출력을 `list()`로 순회해 입력과 `zip` — skip·fail한 인스턴스는 XCom이 없어 인덱스가 밀리고, **다른 행에 결과가 붙는다**
✅ 각 단계가 키를 담은 dict를 통째로 넘긴다. 굳이 위치로 이어야 하면 `map_indexes`를 명시해 당긴다(빈 자리가 `None`으로 남는다)

## 매핑 단계 사이 trigger_rule
❌ 매핑 태스크를 이어 붙이며 기본 `all_success` 두기 — 인스턴스 하나만 skip돼도 하류 단계가 **통째로** skip된다
✅ 행별 실패를 허용할 거면 하류 매핑 단계에 `trigger_rule=all_done`

## asset 트리거 — 이벤트 종류와 timetable 짝 안 맞춤
❌ 상류가 partition_key를 실은 파티션 이벤트를 발행하는데 평면 `schedule=[Asset(...)]`로 구독 — 파티션 이벤트는 평면 컨슈머를 지나치고(`created_dagruns=[]`), 파티션 컨슈머는 pk 없는 이벤트에 반응하지 않는다. 어느 쪽이든 트리거 0건이 조용히 지속된다
✅ 설계 때 발행 이벤트의 pk 유무를 확인하고(이벤트 payload의 `partition_key`), pk가 실리면 `PartitionedAssetTimetable(assets=..., default_partition_mapper=IdentityMapper())`로 구독. 트리거 안 될 땐 이벤트 존재 → `created_dagruns` → 컨슈머 `asset_expression` → `queuedEvents` 순으로 진단
❌ 발행 쪽에서도 짝이 깨진다: outlets 선언 task가 `add_partitions` 호출 없이 성공 종료 — 평면(무파티션) 이벤트가 자동 발행돼 파티션 컨슈머는 무반응, 평면 컨슈머는 "발행할 게 없던 run"에도 오발 트리거된다
✅ 발행할 파티션이 없으면 `AirflowSkipException`으로 skip — skip된 task는 어떤 이벤트도 내지 않는다. `add_partitions`로 pk를 실었으면 평면 이벤트는 함께 나가지 않는다

## 비밀·연결정보 하드코딩
❌ 접속정보·비밀번호·토큰을 코드에 박기
✅ Connection(비밀)·Variable(설정), 코드엔 키 이름만

## task 삭제 (수정·리팩터 시)
❌ 기존 DAG에서 task 제거 (그 task의 실행 이력·로그가 UI에서 끊김)
✅ 되도록 task는 두고 새 DAG로 분리, 꼭 지워야 하면 이력 손실을 인지하고 확인받기

## TLS 검증
❌ `requests`에 `verify=False`로 인증서 검증 끄기
✅ 검증 켜둔다
