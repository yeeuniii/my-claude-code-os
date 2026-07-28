---
type: os-improvement
date: 2026-07-28
subject: 운영 Airflow 3.3.0 업그레이드에 lab 정합화 + verify.sh 결함 2건 수정
---

## 무엇을

운영 Airflow가 3.2.2 → 3.3.0으로 올라간 것에 맞춰 OS를 정합화했다(커밋 `bd3b470`).

- `lab` 환경·문서를 3.3.0으로. 버전 표기는 `setup.sh` 한 곳만 남기고 `SKILL.md`·`dag-tester`·다이어그램 소스에서 제거
- `verify.sh` 결함 2건 수정 — 3.3.0에서 삭제된 `DagBag(include_examples=)` 인자, `UNIT_TEST_MODE=true`
- `context/airflow3-knowledge.md`의 cron 절을 `create_cron_data_intervals`·`logical_date` 기준으로 정확화
- `designs/` 경로 규칙을 `dag-design-spec.md` 한 곳으로 모으고 `<dag_id>[-<목적>].md`로 확장, 참조처 7곳의 하드코딩 제거

발단은 이 작업이 아니었다. googleplay 리뷰 DAG의 수집 창 버그를 진단하다가 운영 `Dockerfile`이 3.3.0인 걸 우연히 보고, lab이 "운영과 동일한 3.2.2"라고 주장하는 것과 어긋난 걸 발견했다.

## 왜 (결정과 트레이드오프)

- **버전 표기를 `setup.sh` 한 곳으로.** 여러 곳에 박아두니 업그레이드 때 실제로 세 곳(`lab/SKILL.md`, `dag-tester.md`, 다이어그램 소스)이 3.2.2에 남아 있었다. 대신 "지금 몇 버전인지" 알려면 `setup.sh`를 열어야 한다 — 그 비용은 감수했다.
- **`UNIT_TEST_MODE`를 덮어쓰지 않고 제거.** `AIRFLOW__SCHEDULER__CREATE_CRON_DATA_INTERVALS=False`로 그 항목만 되돌릴 수도 있었지만, `unit_tests.cfg`가 그 밖에 무엇을 더 뒤집는지 알 수 없어 근본을 택했다. 끄고도 DagBag 로드가 정상임을 실측으로 확인한 뒤 제거.
- **`designs/` 경로를 리네임 대신 규칙 확장으로.** 한 DAG에 작업이 여러 번 생기는 게 실제 패턴이었다(수집 창 핫픽스 먼저, EL/T 구조 개편 나중). `<dag_id>.md` 하나로 강제하면 뒤 작업이 앞 작업의 근거를 덮어쓴다.

## 발견 / 배운 점

- **검증 도구가 조용히 틀린 답을 준다.** `verify.sh`가 켜던 `AIRFLOW__CORE__UNIT_TEST_MODE=true`는 `unit_tests.cfg`를 로드해 `scheduler.create_cron_data_intervals`를 `True`로 뒤집는다. 그 결과 cron DAG가 운영(`CronTriggerTimetable`)과 다른 `CronDataIntervalTimetable`로 파싱된다. 하필 그때 진단하던 DAG 버그의 핵심이 정확히 그 설정이었다 — 이 도구만 믿었으면 **정반대로 진단**했을 것이다.
- **"운영과 동일"이라는 문서의 주장은 아무도 검증하지 않는다.** 스킬 본문에 단언으로 적혀 있으면 그대로 믿게 된다. 실물(운영 `Dockerfile`)과 대조한 계기는 우연이었다.
- **버전 업그레이드는 검증 도구를 조용히 깨뜨린다.** 3.3.0에서 `DagBag.__init__()`의 `include_examples` 인자가 삭제돼 `verify.sh`가 그대로 실패했다. 운영을 올린 시점과 로컬을 맞추는 시점 사이에는 그 사실을 모르는 구간이 있다.
- **격리된 눈이 방금 심은 버그를 잡는다.** `sync`가, 내가 몇 분 전 `lab/SKILL.md`에 쓴 `source <(grep …)`이 macOS 기본 `/bin/bash`(3.2)에서 **조용히 빈 값**을 만든다고 셸별 실측으로 보고했다(zsh에서는 정상이라 내 손에서는 통과했다). 빈 값이면 constraint URL이 `constraints-/constraints-.txt`가 되어 버전 정합이 소리 없이 깨진다. `eval "$(…)"`로 교체.

## 다음에 재사용할 것

- **운영 버전이 올라가면 DAG 작업보다 먼저 `lab`을 맞춘다.** 어긋난 환경에서 나온 검증 결과는 신뢰할 수 없고, 그 사실을 나중에 알면 이미 내린 판단을 전부 되짚어야 한다.
- **로컬 검증 환경에 테스트 전용 모드 플래그를 켜지 않는다.** 편의를 위해 켠 플래그가 운영 기본값을 바꿔버리면 검증의 의미가 사라진다. 운영 재현이 편의보다 우선이다.
- **스케줄·날짜 시맨틱을 검증할 때는 timetable 타입부터 확인하고 시작한다.** cron 문자열이 어떤 timetable로 변환되는지가 `logical_date`의 의미를 결정한다.
- **셸 스니펫을 문서에 넣을 때는 macOS 기본 `/bin/bash`(3.2)에서도 도는지 확인한다.** process substitution(`<(…)`) + `source` 조합은 거기서 동작하지 않는다.
- **같은 값(버전·경로 규칙)이 두 곳 이상에 박히면 단일 출처로 모으고 나머지는 참조만 시킨다.** 이번 정합화에서 실제로 어긋나 있던 것들이 전부 복제된 표기였다.
