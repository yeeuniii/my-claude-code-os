#!/usr/bin/env bash
# os-reminder.sh — OS 자산 편집 시 정합성 흐름을 상기 (비블로킹)
#
# PostToolUse(Edit|Write|MultiEdit) 훅. 편집 대상이 OS 자산
# (.claude/**, OS.md, CLAUDE.md, learnings/**)이면 additionalContext 로
# "os 스킬 흐름(정합성·작성규칙 점검)을 태워라"를 부모 모델에 표면화한다.
# OS 자산이 아니면 조용히 통과. 막지 않고 상기시키기만 하며,
# 사소한 편집은 모델이 판단해 건너뛴다.

set -uo pipefail

# heredoc 이 stdin 을 파이썬 소스 전달에 쓰므로, payload 는 env 로 넘긴다.
_PAYLOAD="$(cat)"; export _PAYLOAD

python3 - <<'PY'
import sys, json, os

try:
    p = json.loads(os.environ.get("_PAYLOAD", "") or "{}")
except Exception:
    sys.exit(0)  # payload 못 읽으면 조용히 통과 (검증 불가 ≠ 실패)

fp = (p.get("tool_input") or {}).get("file_path") or ""
if not fp:
    sys.exit(0)

# repo 루트 기준 상대경로로 판단 (프로젝트 밖 파일이면 상대경로가 ../ 로 시작 → 대상 아님)
proj = os.environ.get("CLAUDE_PROJECT_DIR") or ""
rel = os.path.relpath(fp, proj) if proj else fp

def is_os_asset(r):
    if r.startswith(".claude/"): return True
    if r in ("OS.md", "CLAUDE.md"): return True
    if r.startswith("learnings/"): return True
    return False

if not is_os_asset(rel):
    sys.exit(0)  # OS 자산 아님 → 조용히

msg = (f"📐 OS 자산 편집됨: {rel} — 이건 OS.md·스킬·에이전트·컨텍스트·산출물이 서로 "
       f"맞물린 자산이다. 편집을 마쳤으면 /os 로 정합성·작성규칙을 점검해 "
       f"참조처가 어긋나지 않았는지 확인하라. 오타·한 줄 같은 사소한 편집이면 건너뛴다.")
print(json.dumps({"hookSpecificOutput": {
    "hookEventName": "PostToolUse", "additionalContext": msg}}))
sys.exit(0)
PY
