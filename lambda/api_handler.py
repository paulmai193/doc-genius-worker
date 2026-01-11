import json
import boto3
import uuid
import os
from datetime import datetime, timedelta

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')

INPUT_BUCKET = os.environ['INPUT_BUCKET']
JOB_TABLE = os.environ['JOB_TABLE']
STATE_MACHINE_ARN = os.environ['STATE_MACHINE_ARN']

def handler(event, context):
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Parse multipart form data (simplified for PoC)
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        # For PoC, assume JSON payload with archive and descriptor
        try:
            payload = json.loads(body)
            archive_content = payload.get('archive')
            descriptor = payload.get('descriptor')
        except:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid JSON payload'})
            }
        
        if not archive_content or not descriptor:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Both archive and descriptor required'})
            }
        
        # Store files in S3
        input_key = f"{job_id}/archive.zip"
        descriptor_key = f"{job_id}/descriptor.json"
        
        # Store archive (base64 decoded)
        import base64
        archive_data = base64.b64decode(archive_content)
        s3.put_object(
            Bucket=INPUT_BUCKET,
            Key=input_key,
            Body=archive_data,
            ContentType='application/zip'
        )
        
        # Store descriptor
        s3.put_object(
            Bucket=INPUT_BUCKET,
            Key=descriptor_key,
            Body=json.dumps(descriptor),
            ContentType='application/json'
        )
        
        # Create job record in DynamoDB
        table = dynamodb.Table(JOB_TABLE)
        submit_time = int(datetime.utcnow().timestamp() * 1000)
        expires_at = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        
        table.put_item(
            Item={
                'jobId': job_id,
                'status': 'Pending',
                'submitTime': submit_time,
                'inputKey': input_key,
                'descriptorKey': descriptor_key,
                'expiresAt': expires_at
            }
        )
        
        # Start Step Functions execution
        stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"job-{job_id}",
            input=json.dumps({
                'jobId': job_id,
                'inputKey': input_key,
                'descriptorKey': descriptor_key
            })
        )
        
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'jobId': job_id})
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }