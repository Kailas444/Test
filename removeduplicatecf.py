import pandas as pd
import numpy as np
from pandas.io import gbq
from google.cloud import bigquery
import logging
def gcs_bq_client_dnb_raw(event, context):
    file_name = event['name']
    table_name = '#{GCP_client_dnb_RAW_TABLE}#'
    file_extention = file_name.split('.')[1]
    client = bigquery.Client(project='#{GCP_PROJECT_ID}#') 
    table = client.get_table('#{GCP_TARGET_DS_NAME_RAW_client_dnb_raw}#' +'.'+'#{GCP_client_dnb_RAW_TABLE}#') 
    headers= [field.name for field in table.schema]    
    bq_schema=table.schema
    bq_to_pandas_conv={"STRING":np.dtype("O"),"DATETIME":np.dtype("O")}
    dtypes=[(field.name,bq_to_pandas_conv[field.field_type]) for field in bq_schema]
    dtypes2={field_name: dtype for field_name,dtype in dtypes}
    try:
        if file_extention == 'json':
            df_data = pd.read_json('gs://' + event['bucket'] + '/' + file_name, dtype=dtypes2, header=None, names=headers, skiprows=1).drop_duplicates(subset=['DUNSNbr'], keep='first')         
        elif file_extention == 'csv':
          df_data = pd.read_csv('gs://' + event['bucket'] + '/' + file_name, dtype=dtypes2, header=None, names=headers, skiprows=1).drop_duplicates(subset=['DUNSNbr'], keep='first')
          #if date records are there then include parse_dates=parse_dates in the above row after skiprows
        elif file_extention == 'txt':
          df_data = pd.read_csv('gs://' + event['bucket'] + '/' + file_name,sep = "|", dtype=dtypes2, header=None, names=headers, skiprows=1).drop_duplicates(subset=['DUNSNbr'], keep='first')
          #if date records are there then include parse_dates=parse_dates in the above row after skiprows
    except Exception as e:
          print(f'Error reading file {file_name}: {e}')
          return
    nol = len(df_data)
    blank_key_cols=df_data['DUNSNbr'].isnull().sum()
    df_data= df_data.dropna(subset=['DUNSNbr'])
    nol_new = len(df_data)
    print(f'{nol} is the actual rows in the file after removing duplicates and {blank_key_cols} is the no. of blank DUNSNbr rows and {nol_new} in the final number of rows which will be getting inserted into BQ')
    logging.warning(f'{blank_key_cols} is the no. of blank DUNSNbr')
    df_data=df_data.assign(CreateUserId="xddp-user")
    df_data=df_data.assign(CreateDttm=pd.Timestamp.now())
    df_data=df_data.assign(UpdateUserId="xddp-user")
    df_data=df_data.assign(UpdateDttm=pd.Timestamp.now())
    df_data=df_data.assign(IsActiveInd="Y")
    df_data.to_gbq('#{GCP_TARGET_DS_NAME_RAW_client_dnb_raw}#' +'.'+ table_name, 
                         project_id='#{GCP_PROJECT_ID}#', 
                         if_exists='replace',
                         location='#{GCP_PROJECT_REGION}#')
    print(f'{nol_new} rows inserted into BigQuery!')      
    logging.warning('Sucessfull')
