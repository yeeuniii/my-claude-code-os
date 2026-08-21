# 오퍼레이터 · 작성 스타일

## TaskFlow 표준
- `@dag(...)` + `@task`로 구성한다(진입점은 `airflow.sdk`). 
- 파일 끝에서 `dag_fn()` 인스턴스화. 
- 클래식 `with DAG(...)`는 쓰지 않는다.

## 동적 그래프
- fan-out: `@task.expand()` / `.partial(...).expand(...)`
- 그룹화: 계정·앱별은 `with TaskGroup(group_id=f"...")`
- 같은 task 반복 인스턴스화는 `.override(task_id=...)`

## 선호 오퍼레이터
- 센서: `PythonSensor`/`@task.sensor`, `GCSObjectExistenceSensor`. 모드는 대기 길이로 — 짧으면(몇 분 이내) `poke`, 길면(수십 분 이상) `mode="reschedule"`(슬롯 놓아줌). 아주 길면 deferrable 고려.
- 흐름 제어: `@task.short_circuit`.
- 격리 실행: `@task.external_python`(별도 venv, airbyte), `DockerOperator`(컨테이너 실행).
- 클래식 `BranchPythonOperator`/`PythonOperator` 직접 사용은 피한다(계보용 emit 등 불가피한 곳만).

## 로깅
- `logger = logging.getLogger("airflow.task")`. `print()` 디버깅은 지양.

## 주석·독스트링
- 여러 줄 설명은 **제목 한 줄 + 불릿**. 산문 단락으로 늘어놓지 않는다.
- **불릿 한 줄엔 한 문장만.** 문장이 길어도 중간에 줄을 바꾸지 않고, 한 줄에 문장 두 개를 담지 않는다.
- **현재 사실만** 적는다 — 과거 버전과의 비교, 외부 문서·이슈 참조, 편집 이력은 금지.
  현재 코드가 딛고 선 제약(특정 버전의 동작에 의존 등)은 히스토리가 아니므로 남긴다.

## 방어·검증 최소주의
- 방어 코드는 설계도·컨벤션이 명시한 것만. "혹시 몰라서"는 넣지 않는다.
- 팀 내부에서만 만지는 설정(Variable 등)은 필수 키 강제 대신 **기본값 폴백**을 우선한다.
- 검증은 **무음 실패**(에러 없이 품질이 새는 것)에 집중한다 — 시끄럽게 터지는 결함은 그냥 터지게 둔다.
