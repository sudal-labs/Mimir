"""야간 전체 재인덱싱 DAG.

스케줄: 매일 새벽 2시 (Asia/Seoul)
동작: mimir-index가 노출할 재인덱싱 HTTP 엔드포인트를 호출한다.
      (엔드포인트는 mimir-index 구현 단계에서 확정)

의사결정 사이클 상태: 🟡 제안 — 구체적 스케줄/DAG 구조는 mimir-scheduler 구현 시점에 확정.
"""
from datetime import timedelta

from airflow import DAG
from airflow.operators.http import SimpleHttpOperator
from airflow.utils.dates import days_ago

DEFAULT_ARGS = {
    "owner": "mimir",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="nightly_reindex",
    default_args=DEFAULT_ARGS,
    description="전체 vault 재인덱싱 (야간 배치)",
    schedule_interval="0 2 * * *",
    start_date=days_ago(1),
    catchup=False,
    tags=["mimir", "index"],
) as dag:
    triggerReindex = SimpleHttpOperator(
        task_id="trigger_full_reindex",
        http_conn_id="mimir_index",
        endpoint="/reindex/full",
        method="POST",
        response_check=lambda response: response.status_code == 200,
        dag=dag,
    )
