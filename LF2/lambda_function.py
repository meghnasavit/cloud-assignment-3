# Search Photo Version 2 updated by codepipeline
import json
import random
import boto3
import botocore
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

lex_v2 = boto3.client('lexv2-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    query = event.get('queryStringParameters', {}).get('q', '')
    print("Query",query)

    if not query:
        return {
            'statusCode': 400,
            'body': json.dumps('No search query provided')
        }
    
    labels = get_labels(query)
    
    print("Labels",labels)
    
    if len(labels) != 0:
        img_path = get_photo_path(labels)
        
    if not img_path:
        return{
            'statusCode':200,
            "headers": {"Access-Control-Allow-Origin":"*"},
            'body': json.dumps('No Results found')
        }
    else:    
        return{
            'statusCode': 200,
            'headers': {"Access-Control-Allow-Origin":"*"},
            'body': json.dumps({
                'imagePaths':img_path,
                'userQuery':query,
                'labels': labels,
            }),
            'isBase64Encoded': False
        }
    
    

def get_labels(query):
    sample_string = 'abcdefghijklmnopq'
    user_id = ''.join((random.choice(sample_string)) for _ in range(8))

    print(query)

    try:
        # Call post_text operation for Lex V2
        response = lex_v2.recognize_text(
            botId='SNGPPYUAFC',
            botAliasId='TSTALIASID',
            localeId='en_US', 
            sessionId=user_id,
            text=query
        )
        print("lex-response", response)
        
        data = response

        interpreted_values = []
        for value in data["sessionState"]["intent"]["slots"]["QuerySlot"]["values"]:
            interpreted_values.append(value["value"]["interpretedValue"].lower())

        print("Interpreted_Values",interpreted_values)
        return interpreted_values

        # Process the response as needed
    except botocore.exceptions.ClientError as e:
        print(f"Error calling Lex V2: {e}")
        
def get_photo_path(keys):
    host = os.environ['ES_HOST'] 
    region = 'us-east-1'
    es_index = 'photos'

    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

    es = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )
    resp = []
    searchData = es.search({"query": {"terms": {"labels": keys}}})
    resp.append(searchData)
    print("Version 2 Lambda running")
    print("response of open", resp)

    output = []
    for r in resp:
        if 'hits' in r:
             for val in r['hits']['hits']:
                key = val['_source']['objectKey']
                if key not in output:
                    output.append('https://photo-bucket-meghna.s3.us-east-1.amazonaws.com/'+key)
    print ("outpout please", output)
    return output
