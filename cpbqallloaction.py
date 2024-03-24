import csv
import datetime
import io
import logging

from airflow import models
from airflow.contrib.operators import bigquery_to_gcs
from airflow.contrib.operators import gcs_to_bq
from airflow.operators import dummy_operator
# Import operator from plugins


# --------------------------------------------------------------------------------
# Set default arguments
# --------------------------------------------------------------------------------

default_args = {
    'owner': 'airflow',
    'start_date': datetime.datetime.today(),
    'depends_on_past': False,
    'email': [''],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': datetime.timedelta(minutes=5),
}

# --------------------------------------------------------------------------------
# Set variables
# --------------------------------------------------------------------------------

# 'table_list_file_path': This variable will contain the location of the master
# file.
table_list_file_path = models.Variable.get('table_list_file_path')

# Source Bucket
source_bucket = models.Variable.get('gs://bq_to_gcs_csvdata')

# Destination Bucket
dest_bucket = models.Variable.get('gcs_dest_bucket')

# --------------------------------------------------------------------------------
# \

# --------------------------------------------------------------------------------

logger = logging.getLogger('bq_copy_us_to_eu_01')

# --------------------------------------------------------------------------------
# Functions
# --------------------------------------------------------------------------------


def read_table_list(table_list_file):
    """
    Reads the table list file that will help in creating Airflow tasks in
    the DAG dynamically.
    :param table_list_file: (String) The file location of the table list file,
    e.g. '/home/airflow/framework/table_list.csv'
    :return table_list: (List) List of tuples containing the source and
    target tables.
    """
    table_list = []
    logger.info('Reading table_list_file from : %s' % str(table_list_file))
    try:
        with io.open(table_list_file, 'rt', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # skip the headers
            for row in csv_reader:
                logger.info(row)
                table_tuple = {
                    'table_source': row[0],
                    'table_dest': row[1]
                }
                table_list.append(table_tuple)
            return table_list
    except IOError as e:
        logger.error('Error opening table_list_file %s: ' % str(
            table_list_file), e)


# --------------------------------------------------------------------------------
# Main DAG
# --------------------------------------------------------------------------------

# Define a DAG (directed acyclic graph) of tasks.
# Any task you create within the context manager is automatically added to the
# DAG object.
with models.DAG('bq_copy_us_to_eu_01',
                default_args=default_args,
                schedule_interval=None) as dag:
    start = dummy_operator.DummyOperator(
        task_id='start',
        trigger_rule='all_success'
    )

    end = dummy_operator.DummyOperator(
        task_id='end',

        trigger_rule='all_success'
    )

    # Get the table list from master file
    all_records = read_table_list(table_list_file_path)

    # Loop over each record in the 'all_records' python list to build up
    # Airflow tasks
    for record in all_records:
        logger.info('Generating tasks to transfer table: {}'.format(record))

        table_source = record['table_source']
        table_dest = record['table_dest']

        BQ_to_GCS = bigquery_to_gcs.BigQueryToCloudStorageOperator(
            # Replace ":" with valid character for Airflow task
            task_id='{}_BQ_to_GCS'.format(table_source.replace(":", "_")),
            source_project_dataset_table=table_source,
            destination_cloud_storage_uris=['{}-*.avro'.format(
                'gs://' + source_bucket + '/' + table_source)],
            export_format='AVRO'
        )

        start >> BQ_to_GCS >> end
