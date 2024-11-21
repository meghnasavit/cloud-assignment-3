# Index Photo Version 2 updated by codepipeline
import boto3 
import json
import os 
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

s3_client = boto3.client('s3')
rekognition_client = boto3.client('rekognition', region_name='us-east-1')

# Elasticsearch configuration
host = os.environ['ES_HOST'] 
region = 'us-east-1'
es_index = 'photos'

credentials = boto3.Session().get_credentials()
print("CREDENTIALS")
print(credentials.access_key, credentials.secret_key, credentials.token)
#awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)
awsauth = AWS4Auth(region='us-east-1', service='es', refreshable_credentials=credentials)
es = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)

def lambda_handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']
    print("event",event)
    
    response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
    print(response)
    
    custom_labels = response['ResponseMetadata']['HTTPHeaders'].get('x-amz-meta-customlabels', '')
    if custom_labels:
        custom_labels_list = [label.strip() for label in custom_labels.lower().split(',')]
    else:
        custom_labels_list = []
    print("custom labels",custom_labels)
    
    rekognition_response = rekognition_client.detect_labels(
        Image={'S3Object': {'Bucket': bucket_name, 'Name': object_key}},
        MaxLabels=10
    )
    detected_labels = [label['Name'].lower() for label in rekognition_response['Labels']]

    print("DETECTED LABELS")
    print(detected_labels)
    
    labels = list(set(custom_labels_list + detected_labels))
    
    doc = {
        'objectKey': object_key,
        'bucket': bucket_name,
        'createdTimestamp': datetime.now().isoformat(),
        'labels': labels
    }
    es.index(index=es_index, body=doc)
    
    print("Siuuuu V3")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Document indexed successfully.')
    }
