# 용어 (OS 문서 공통)

**같은 의미에는 같은 단어를 쓴다.** 금지 목록이 아니라 통일 원칙이다 — 아래 의미를 가리킬 때는 아래 단어로만 부른다.

| 용어 | 의미 |
| --- | --- |
| **source** | 데이터가 오는 곳 — 외부 시스템·테이블·엔드포인트 |
| **destination** | 이 DAG가 **쓰는** 테이블 |
| **downstream** | destination을 **읽는** 쪽 — 다음 DAG·대시보드·사람 |

같은 의미를 다른 단어(원천, upstream, 목적지, target, 소비자)로 갈아타지 않는다.

Airflow 문법의 task upstream/downstream(한 DAG 안 task 선후 관계)은 별개 문맥이다 — 이 표의 용어와 혼동하지 않는다.
