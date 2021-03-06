# [START import_module]
from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import timedelta
from datetime import datetime
from airflow.operators.bash import BashOperator
# [END import_module]

# [START default_args]
default_args = {
  'owner': 'Otávio Faria',
  'depends_on_past': False,
  'email': ['otavio.faria@alphabot.com.br'],
  'email_on_failure': True,
  'email_on_retry': False,
  'retries': 3,
  'retry_delay': timedelta(minutes=0.1)
}
# [END default_args]

# [START instantiate_dag]
dag = DAG(
  'extract-data',
  default_args=default_args,
  start_date=datetime(2022, 1, 25),
  schedule_interval='@weekly',
  tags=['extract', 'inbound', 'S3']
)
# [END instantiate_dag]

# [START functions]
def get_data_yahoo_finances():
  import pandas as pd
  import boto3
  from urllib.request import urlopen
  from airflow.models import Variable
  import json

  # [START env_variables]
  ACCESS_KEY = Variable.get("ACCESS_KEY")
  SECRET_ACCESS = Variable.get("SECRET_KEY")
  # [END env_variables]

  tickers = [
    'AAPL',
    'VALE'
  ]
		
  bucket_name = "yahoo-finances-bg"

  s3 = boto3.resource( 's3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_ACCESS)
  bucket_name = "yahoo-finances-bg"

  for ticker in tickers:
    url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + ticker + '?interval=1h'
    response = urlopen(url)

    data_json = json.loads(response.read())
    data_timestamp = data_json['chart']['result'][0]['timestamp']
    data_json = data_json['chart']['result'][0]['indicators']['quote']
    df = pd.DataFrame.from_dict(data_json[0])
    df['timestamp'] = data_timestamp
    df['ticker'] = ticker
    df['year'] = datetime.now().year
    df['month'] = datetime.now().month
    df['day'] = datetime.now().day

    bytes_to_write = df.to_csv(None, index=False).encode()
    folder_name = f'inbound/{datetime.now().year}/{datetime.now().month}/{ticker}'
    s3.Object(bucket_name=bucket_name, key=f'{folder_name}/finances_{ticker}_{datetime.now().day}.csv').put(Body=bytes_to_write)
# [END functions]

extract_data_yahoo_finances = PythonOperator(
  task_id='extract_data_yahoo_finances',
  python_callable=get_data_yahoo_finances,
  dag=dag
)

extract_data_yahoo_finances