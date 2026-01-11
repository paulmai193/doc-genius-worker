import json
import boto3
import os
from datetime import datetime

sns = boto3.client('sns')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET')
JOB_TABLE = os.environ['JOB_TABLE']

def success_handler(event, context):
    """Handle successful job completion notification"""
    try:
        job_id = event['jobId']
        output_key = event.get('outputKey')
        
        # Generate presigned URL if output exists
        download_url = None
        if output_key and OUTPUT_BUCKET:
            download_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': OUTPUT_BUCKET, 'Key': output_key},
                ExpiresIn=86400  # 24 hours
            )
        
        # Prepare notification message
        message = {
            'jobId': job_id,
            'status': 'Succeeded',
            'timestamp': int(datetime.utcnow().timestamp() * 1000),
            'downloadUrl': download_url,
            'metadata': {
                'module': 'Generated via AI Digital Worker',
                'processingComplete': True
            }
        }
        
        # Publish to SNS
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f'Digital Worker Job {job_id} Completed Successfully'
        )
        
        return {'status': 'notification_sent'}
        
    except Exception as e:
        print(f"Error sending success notification: {str(e)}")
        return {'status': 'notification_failed', 'error': str(e)}

def failure_handler(event, context):
    """Handle failed job notification"""
    try:
        job_id = event['jobId']
        error_message = event.get('errorMessage', 'Unknown error')
        
        # Prepare notification message
        message = {
            'jobId': job_id,
            'status': 'Failed',
            'timestamp': int(datetime.utcnow().timestamp() * 1000),
            'errorMessage': error_message,
            'metadata': {
                'module': 'AI Digital Worker',
                'processingComplete': False
            }
        }
        
        # Publish to SNS
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message),
            Subject=f'Digital Worker Job {job_id} Failed'
        )
        
        return {'status': 'notification_sent'}
        
    except Exception as e:
        print(f"Error sending failure notification: {str(e)}")
        return {'status': 'notification_failed', 'error': str(e)}