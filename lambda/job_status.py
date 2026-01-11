import json
import boto3
import os
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

JOB_TABLE = os.environ['JOB_TABLE']
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']

def handler(event, context):
    try:
        job_id = event['pathParameters']['jobId']
        
        # Get job from DynamoDB
        table = dynamodb.Table(JOB_TABLE)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Job not found'})
            }
        
        job = response['Item']
        
        result = {
            'jobId': job_id,
            'status': job['status']
        }
        
        # Add download URL if succeeded
        if job['status'] == 'Succeeded' and 'outputKey' in job:
            try:
                download_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': OUTPUT_BUCKET, 'Key': job['outputKey']},
                    ExpiresIn=86400  # 24 hours
                )
                result['downloadUrl'] = download_url
            except ClientError as e:
                print(f"Error generating presigned URL: {e}")
        
        # Add error message if failed
        if job['status'] == 'Failed' and 'errorMessage' in job:
            result['errorMessage'] = job['errorMessage']
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Internal server error'})
        }