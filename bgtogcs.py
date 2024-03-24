from airflow import DAG
from airflow.contrib.operators import bigquery_to_gcs
from datetime import datetime, timedelta

from airflow.models import Variable, TaskInstance
from airflow.operators.python_operator import PythonOperator
import datetime
from airflow import models
from airflow.utils import trigger_rule
import logging
from datetime import date, timedelta
from airflow.utils.dates import days_ago
import logging
import os
import sys

default_args = {
    'start_date':days_ago(0)
}

dag = DAG(
    'bqtogcs_datalake',
    default_args=default_args,
    description='Transfer data from a BigQuery table to a GCS bucket',
    schedule_interval=timedelta(days=1),
)

export_command = """
bq extract \
--compression GZIP \
--destination_format CSV \
--field_delimiter ',' \
--print_header \
project_id:dataset.table \
gs://bucket/path/to/output.csv.gz
"""

export_to_gcs = PythonOperator(
    task_id='export_to_gcs',
    dag=dag,
)

export_to_gcs = bigquery_to_gcs.BigQueryToGCSOperator(
    task_id='export_to_gcs',
    source_project_dataset_table='table_name',
    destination_cloud_storage_uris=['gs://bgtogcs_stg_csv/output.csv'],
    export_format='CSV',
    field_delimiter=',',
    print_header=True,
    dag=dag,
)

start >> export_to_gcs


