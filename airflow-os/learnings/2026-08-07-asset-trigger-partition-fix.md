---
type: task
date: 2026-08-07
subject: 파티션 asset 트리거 버그 발견·수정 + batch_cap 실측 상향 + 레거시 백필
dag_id: doris_cx_silver_store_reviews_llm
---

## 무엇을
배포 당일 후속 사이클 셋. ① LLM DAG 2개(helpshift·store)가 asset 이벤트에 한 번도 트리거되지 않는 버그를 발견해 `PartitionedAssetTimetable`로 수정(2612.3.2), ② `batch_cap` 기본값을 커서 실측 근거로 200→1024 상향(2612.3.3), ③ MariaDB 레거시 구글 리뷰 5,226행(2026-01-01~)을 raw로 일회성 백필하고 LLM 백로그 672행 처리.

## 왜 (결정과 트레이드오프)
- **소비자 쪽 수정(파티션 timetable)을 택함**: 이 레포의 asset 체계는 pk 릴레이다 — 최상위 cron이 날짜 pk를 찍고 IdentityMapper로 물려 내려간다. 발행 쪽을 평면 이벤트로 바꾸는 건 체인 전체를 깨므로, 소비자가 파티션 timetable로 구독하는 게 유일한 합류 방법. 커서 DAG라 pk는 트리거 신호+런 라벨로만 쓰고 처리 범위는 계속 커서 소관(pk로 범위를 자르면 재수정·실패분 재시도가 깨진다).
- **batch_cap 1024**: helpshift 커서 실측이 일 61~175행(증가 추세)으로 200에 근접 — asset 이벤트가 하루 1회라 초과분은 통째로 다음 날로 밀려 누적된다. cap은 상한일 뿐이라 평상시 비용 영향 없음. 대가는 돌발 백로그 시 비용 가드가 5배 느슨해지는 것.
- **레거시 백필은 raw 직접 INSERT**: silver는 dbt 풀 리빌드라 직접 넣으면 다음 런에 증발 — raw에 넣어야 파이프라인이 동일하게 처리한다. dbt에 union을 넣는 대안은 스펙("silver는 두 raw 조인이 전부")과 충돌해 기각. 컬럼은 silver가 읽는 것만 매핑, 신·구 review_id가 같은 UUID 공간임을 실측 확인 후 upsert로 겹침 해소.

## 발견 / 배운 점
- **파티션 asset 이벤트와 평면 `[Asset]` 스케줄은 서로 안 물린다.** pk 실린 이벤트는 `created_dagruns=[]`로 평면 컨슈머를 지나치고, 파티션 컨슈머는 pk 없는 이벤트에 반응 안 한다(팩토리 주석+prod 실측). 설계 때 "asset 발행 확인"까지만 보고 **발행 이벤트의 종류(pk 유무)와 컨슈머 timetable의 짝**은 대조하지 않아 두 DAG가 같은 구멍으로 나갔다.
- **진단 경로가 유효했다**: 이벤트 존재(assets/events) → `created_dagruns` → 컨슈머 구독(asset_expression) → queuedEvents 순으로 좁히면 발행/구독/스케줄러 중 어디가 문제인지 갈린다.
- **dev 검증 수단**: `_common/asset_event.py`의 REST 발행(`POST /api/v2/assets/events` + partition_key)으로 상류 없이 파티션 이벤트를 인공 발화할 수 있다 — 수정 후 15초 만에 asset_triggered 런 생성으로 실증.
- 설계 때의 볼륨 실측(일 +77)은 **신규 행 기준**이었고 커서는 재갱신도 집는다 — cap 결정은 신규가 아니라 **커서 걸림 행수**로 재야 한다.
- merge-on-write upsert 백필에서 겹침 구간은 **나중에 쓴 쪽이 이긴다** — 레거시가 EL 최신본을 덮을 수 있음을 사전에 따져야 한다(이번엔 17건, EL 재조회로 자연 치유 범위).
- 커밋 시점에 다른 세션의 staged 변경(레거시 DAG 삭제)이 섞여 들어갔다 — `git add <특정 파일>`이어도 **기존 index의 staged 항목은 커밋에 딸려 온다**. reset 후 분리 커밋으로 수습.

## 다음에 재사용할 것
- **asset 트리거 DAG 설계 체크리스트에 추가**: 발행 이벤트에 partition_key가 실리는지 확인하고, 실리면 소비자는 `PartitionedAssetTimetable(assets=..., default_partition_mapper=IdentityMapper())`로 구독한다. 평면 `[Asset]`은 이 레포의 dbt/airbyte 체인에서 영원히 안 물린다.
- 트리거 안 될 때 진단 순서: 이벤트 존재 → `created_dagruns` → `asset_expression` → `queuedEvents`.
- dev에서 asset 트리거 실험: REST 파티션 이벤트 발행 헬퍼 패턴 (`_common/asset_event.py`).
- batch_cap류 상한은 소스 신규 행수가 아니라 **커서 걸림 행수 실측**(일별 GROUP BY)으로 정한다.
- 운영 레포 커밋 전 `git status`로 **staged 잔여물 확인** — 다른 세션과 워킹트리를 공유한다.
