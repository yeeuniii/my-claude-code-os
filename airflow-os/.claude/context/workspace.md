# 작업환경

## 코드 위치
- 실제 운영 DAG는 운영 레포 `/Users/yepark/Project/airflow.datawave.co.kr/`의 `dags/`. 여기가 **배포 타깃**이다.
- 이 경로는 `.claude/settings.json`의 `additionalDirectories`로 워크스페이스에 등록돼 있어 Glob/Grep/Read가 그대로 동작한다.
- 레포가 이동하면 여기·`CLAUDE.md`·`.claude/settings.json`·`.claude/skills/lab/scripts/verify.sh`를 함께 고친다.

## 구현 위치
- 새 DAG·수정은 운영 레포 `dags/<서브경로>/`에 쓴다. 서브경로·네이밍·구조는 그 폴더의 유사 DAG 관례를 따른다.

## 테스트 위치
- 테스트 코드는 운영 레포 `tests/`에 두고, `dags/`의 서브경로를 미러한다: `dags/<서브폴더>/x.py` → `tests/<서브폴더>/test_x.py`.
- **`dags/` 폴더 안에는 테스트 파일을 절대 두지 않는다.** Airflow DagBag이 그 폴더를 스캔해 모든 `.py`를 DAG로 파싱하므로, 테스트가 파싱 대상에 섞여 에러를 낸다.
- 운영 레포의 `tests/`는 **로컬 마이그레이션 검증용이며 커밋하지 않는다**(운영 레포 `.git/info/exclude`로 로컬 제외).
