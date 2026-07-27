#!/usr/bin/env bash
# 작업 대상 DAG 파일/폴더를 DagBag으로 로드해 import 에러를 검사한다. 성공 기준: 에러 0건.
# 사용법: verify.sh <DAG 파일|폴더>
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "사용법: verify.sh <DAG 파일|폴더>" >&2
    exit 2
fi
TARGET="$1"

cd "$(dirname "$0")/../../../.."  # airflow-os 루트로 이동

AIRFLOW_REPO=/Users/yepark/Project/airflow.datawave.co.kr
if [ ! -d "$AIRFLOW_REPO" ]; then
    echo "운영 레포를 찾을 수 없음: $AIRFLOW_REPO" >&2
    echo "경로가 바뀌었으면 .claude/context/workspace.md의 '코드 위치'를 따라 함께 갱신할 것." >&2
    exit 1
fi

export AIRFLOW_HOME="$PWD/.airflow"
export AIRFLOW__CORE__LOAD_EXAMPLES=false
export AIRFLOW__CORE__UNIT_TEST_MODE=true
# docker-compose.yml의 PYTHONPATH 대응 (config:dags:plugins)
export PYTHONPATH="${AIRFLOW_REPO}/config:${AIRFLOW_REPO}/dags:${AIRFLOW_REPO}/plugins"
# 로컬 더미 Variables 주입 (모듈 최상단 Variable.get() 대응)
source .claude/skills/lab/local_variables.env

.venv/bin/python - "$TARGET" <<'EOF'
import sys
from airflow.dag_processing.dagbag import DagBag

dag_folder = sys.argv[1]
db = DagBag(dag_folder=dag_folder, include_examples=False)

print(f"\nDAG {len(db.dags)}개 로드됨")
if db.import_errors:
    print(f"❌ import error {len(db.import_errors)}건:")
    for path, err in db.import_errors.items():
        print(f"\n--- {path}\n{err}")
    sys.exit(1)
print("✅ import error 0건")
EOF
