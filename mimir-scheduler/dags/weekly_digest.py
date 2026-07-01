"""주간 학습 다이제스트 생성 DAG.

스케줄: 매주 월요일 오전 8시 (Asia/Seoul)
동작:
    1. 지난 주 추가/수정된 노트 목록을 PostgreSQL에서 조회한다.
    2. mimir-api를 통해 LLM에게 주간 다이제스트 작성을 요청한다.
    3. 결과를 vault에 weekly-digest 노트로 커밋한다. (구현 예정)

의사결정 사이클 상태: 🟡 제안 — 구체적 구현은 mimir-scheduler 구현 시점에 확정.
"""
from datetime import timedelta

from airflow import DAG
from airflow.operators.http import SimpleHttpOperator
from airflow.utils.dates import days_ago

DEFAULT_ARGS = {
    "owner": "mimir",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="weekly_digest",
    default_args=DEFAULT_ARGS,
    description="주간 학습 다이제스트 생성 및 vault 커밋",
    schedule_interval="0 8 * * 1",
    start_date=days_ago(1),
    catchup=False,
    tags=["mimir", "digest"],
) as dag:
    generateDigest = SimpleHttpOperator(
        task_id="generate_weekly_digest",
        http_conn_id="mimir_api",
        endpoint="/api/v1/digest/weekly",
        method="POST",
        response_check=lambda response: response.status_code == 200,
        dag=dag,
    )
