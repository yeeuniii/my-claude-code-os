#!/usr/bin/env bash
# Airflow 로컬 테스트 환경 구축 (운영 서버와 동일 버전)
# 철학: 최소 설치. provider·라이브러리는 작업할 DAG가 필요로 할 때 그때그때 추가한다.
#
# 버전은 운영 레포의 Dockerfile(`FROM apache/airflow:<버전>-python<파이썬>`)을 따른다.
# 운영이 올라가면 아래 두 값을 그에 맞춰 바꾸고 이 스크립트를 다시 돌린다.
set -euo pipefail

cd "$(dirname "$0")/../../../.."  # airflow-os 루트로 이동

AIRFLOW_VERSION=3.3.0
PYTHON_VERSION=3.12
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

echo "── 1. venv 생성 (.venv, python ${PYTHON_VERSION})"
uv venv .venv --python ${PYTHON_VERSION}

echo "── 2. Airflow 코어 설치 (constraint 적용)"
uv pip install --python .venv/bin/python --constraint "${CONSTRAINT_URL}" \
    "apache-airflow==${AIRFLOW_VERSION}"

echo "── 3. 단위 테스트 러너 (pytest, constraint 적용)"
uv pip install --python .venv/bin/python --constraint "${CONSTRAINT_URL}" pytest

echo "── 4. DAG별 추가 패키지 (작업하며 그때그때 추가된 것)"
# 스프레드시트 소스 적재 DAG: gspread, google provider(GoogleBaseHook)
uv pip install --python .venv/bin/python --constraint "${CONSTRAINT_URL}" \
    gspread apache-airflow-providers-google

# LLM enrichment DAG: openai provider(OpenAIHook), Doris 적재(MySqlHook)
uv pip install --python .venv/bin/python --constraint "${CONSTRAINT_URL}" \
    apache-airflow-providers-openai apache-airflow-providers-mysql

# doris fastlog 적재 DAG: S3(SeaweedFS) 접근
uv pip install --python .venv/bin/python --constraint "${CONSTRAINT_URL}" boto3

# fastlog ETL DAG: DockerOperator (ephemeral 컨테이너 실행)
uv pip install --python .venv/bin/python --constraint "${CONSTRAINT_URL}" \
    apache-airflow-providers-docker

echo "── 완료. 패키지 추가는 SKILL.md의 '패키지 추가' 절 참고."
