from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryToGCSOperator
from airflow.operators.bash_operator import BashOperator
from datetime import datetime, timedelta

# Set default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 3, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
dag = DAG(
    'bq_to_gcs_csv',
    default_args=default_args,
    description='Export data from BigQuery to GCS in CSV format',
    schedule_interval=timedelta(days=1),
)

# Define the BigQuery query
query = """
    SELECT *
    FROM `sbx-196865-xddpfb4-bd-8e3c7b5d.dlt_mdm_raw_196865.client_dnb_raw`
"""

# Define the BigQuery to GCS operator
bq_to_gcs = BigQueryToGCSOperator(
    task_id='bq_to_gcs',
    source_project_dataset_table='sbx-196865-xddpfb4-bd-8e3c7b5d.dlt_mdm_raw_196865.client_dnb_raw',
    destination_cloud_storage_uris=['gs://bgtogcs_stg_csv/my-file.csv'],
    export_format='CSV',
    field_delimiter=',',
    write_disposition='WRITE_TRUNCATE',
    bigquery_conn_id='bigquery_default',
    google_cloud_storage_conn_id='google_cloud_storage_default',
    dag=dag,
)

# Define a Bash operator to print the GCS object's content
print_gcs_object = BashOperator(
    task_id='print_gcs_object',
    bash_command='gsutil cat gs://bgtogcs_stg_csv/my-file.csv',
    dag=dag,
)

# Set the task dependencies
bq_to_gcs >> print_gcs_object
