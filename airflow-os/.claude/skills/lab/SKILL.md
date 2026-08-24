---
name: lab
description: Airflow 로컬 테스트 환경(venv)을 구축·검증·유지보수하는 인프라 스킬. 사용자가 "로컬 환경 구축/재구축", "환경 검증", "DAG 파싱 테스트", "패키지/더미 값 추가"를 요청하거나, 운영 Airflow 버전이 올라가 로컬을 맞춰야 하거나, DAG 테스트 중 import 에러가 환경 문제로 의심될 때 사용.
---

# Airflow Local Test Environment

**운영 서버와 동일 버전**의 Airflow 로컬 venv 환경.
도커 없이 DAG 파싱 검증·pytest 단위 테스트까지 커버한다.

버전은 운영 레포 `Dockerfile`의 베이스 이미지를 따르며, 실제 설치 값은 `scripts/setup.sh`의 `AIRFLOW_VERSION`·`PYTHON_VERSION`에 있다. **버전이 적힌 곳은 거기 한 곳이다** — 운영이 올라가면 그 두 값만 바꾸고 재구축한다.

**철학: 최소 세팅 + 점진 추가.** 기본은 Airflow 코어이고, provider·라이브러리·더미 Variable/Connection은 **작업하는 DAG가 필요로 할 때 그때그때 추가**해 setup.sh에 누적한다. 운영 DAG 전체를 로컬에서 파싱 가능하게 만드는 것은 목표가 아니다.

## 환경 정보

- 운영 Airflow 레포: 경로는 `.claude/context/workspace.md`의 '코드 위치' 참고 (`verify.sh`가 같은 경로를 PYTHONPATH로 잡는다)
- venv: `airflow-os/.venv` / AIRFLOW_HOME: `airflow-os/.airflow` (SQLite, 운영 DB에 붙지 않음)
- DAG 소스: 운영 레포의 `dags/`를 경로로 직접 참조 (항상 운영 실시간, 복사하지 않음)

## 구축 / 재구축

```bash
bash .claude/skills/lab/scripts/setup.sh   # 코어 + setup.sh에 누적된 DAG별 패키지
```

재구축은 `rm -rf .venv` 후 다시 실행. (재구축하면 그동안 추가한 패키지가 사라지므로, 추가한 패키지는 아래 '패키지 추가' 규칙대로 setup.sh에 기록해둘 것.)

## 검증 (작업 대상 DAG 파싱 체크)

```bash
bash .claude/skills/lab/scripts/verify.sh <DAG 파일|폴더>   # 2~3초
```

타깃은 **운영 레포의 절대경로**로 준다.

- **성공 기준: import error 0건.**
- 에러가 나면 원인 별 대응:
  - `ModuleNotFoundError` → 아래 '패키지 추가'
  - `Variable ... does not exist` / `conn_id ... isn't defined` → 아래 '더미 값 추가'
  - 그 외 → DAG 자체 버그. 코드 수정 대상으로 보고.

## mapped task unmap 검증

expand 를 쓰는 task 의 kwarg 는 파싱이 검증하지 않는다 — 검증이 unmap(런타임)으로 지연되므로,
mapped task 가 있으면 파싱 후 unmap 을 실행해 본다. 태스크 실제 실행이 아니라 kwarg 바인딩 검증이라
이 환경에서 된다:

```python
# .venv 파이썬으로 실행 — DagBag 로드 후 mapped task 를 unmap
# 데코레이터 기반 mapped task 는 unmap(None) 이 안 된다 — SDK 가 mapped_kwargs["op_kwargs"] 를
# 첨자 접근하므로, 해석된 kwargs 형태로 넘겨야 kwarg 바인딩까지 검증된다.
dag = DagBag(<폴더>).get_dag("<dag_id>")
for t in dag.tasks:
    if hasattr(t, "unmap"):
        t.unmap({"op_kwargs": {<expand 인자명>: <샘플 값>}})   # 잘못된 kwarg 면 TypeError
```

- **성공 기준: unmap TypeError 0건.**

## 패키지 추가

```bash
# airflow 생태계 패키지는 반드시 constraint 적용. 버전은 setup.sh에서 읽어 쓴다.
eval "$(grep -E '^(AIRFLOW|PYTHON)_VERSION=' .claude/skills/lab/scripts/setup.sh)"
uv pip install --python .venv/bin/python \
  --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt" \
  <package>
```

추가했으면 **setup.sh에도 한 줄 반영** (재구축 시 유실 방지). 공개 PyPI에 없는 사내 패키지(예: `dough`)는 setup.sh의 해당 설치 줄(사내 레지스트리 `--extra-index-url`)을 그대로 재실행한다.

## 더미 값 추가 (Variable / Connection)

DAG가 파싱 시점에 Variable/Connection을 조회하면 `local_variables.env`에 더미를 추가한다:

- Variable: `export AIRFLOW_VAR_<KEY>="dummy"` (JSON형은 코드가 참조하는 키 구조까지 맞출 것)
- Connection: `export AIRFLOW_CONN_<ID>="mysql://dummy:dummy@localhost:3306/dummy"`
- **실제 운영 값은 절대 넣지 않는다.** verify.sh가 이 파일을 자동으로 로드한다.

## 알려진 한계

- 사내 라이브러리 `dough`는 사내 PyPI 레지스트리에서 설치된다(setup.sh에 반영됨). 다만 **파싱 시점에** dough로 운영 메타DB를 조회하는 DAG(앱 목록으로 fan-out을 정하는 유형)는 사내망이 닿아야 파싱된다(dough 내장 db.cfg, env로 우회 불가) — 안 닿으면 환경 문제가 아니므로 시간 쓰지 말 것. task 안에서만 dough를 쓰는 DAG는 사내망 없이도 파싱된다.
- 이 환경은 파싱·단위 테스트용. 태스크 실제 실행(통합 테스트)이 필요해지면 2단계 도커 환경을 별도 구축한다. (mapped task unmap 검증은 실행이 아니라 kwarg 바인딩 검증이라 여기서 된다 — 위 소절.)
