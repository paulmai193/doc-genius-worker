import json
import boto3
import os
from datetime import datetime, timedelta

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

INPUT_BUCKET = os.environ['INPUT_BUCKET']
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
JOB_TABLE = os.environ['JOB_TABLE']

def handler(event, context):
    """Clean up expired job artifacts"""
    try:
        # Handle both Step Functions invocation and EventBridge scheduled runs
        job_id = event.get('jobId')
        
        if job_id:
            # Direct cleanup for specific job
            cleanup_job(job_id)
        else:
            # Scheduled cleanup - find expired jobs
            cleanup_expired_jobs()
        
        return {'status': 'cleanup_completed'}
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        return {'status': 'cleanup_failed', 'error': str(e)}

def cleanup_job(job_id):
    """Clean up artifacts for a specific job"""
    try:
        # Get job details
        table = dynamodb.Table(JOB_TABLE)
        response = table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            print(f"Job {job_id} not found")
            return
        
        job = response['Item']
        
        # Delete input files
        if 'inputKey' in job:
            try:
                s3.delete_object(Bucket=INPUT_BUCKET, Key=job['inputKey'])
                print(f"Deleted input: {job['inputKey']}")
            except Exception as e:
                print(f"Error deleting input {job['inputKey']}: {e}")
        
        if 'descriptorKey' in job:
            try:
                s3.delete_object(Bucket=INPUT_BUCKET, Key=job['descriptorKey'])
                print(f"Deleted descriptor: {job['descriptorKey']}")
            except Exception as e:
                print(f"Error deleting descriptor {job['descriptorKey']}: {e}")
        
        # Delete output files (optional - may keep for download period)
        if job.get('status') == 'Failed' and 'outputKey' in job:
            try:
                s3.delete_object(Bucket=OUTPUT_BUCKET, Key=job['outputKey'])
                print(f"Deleted failed output: {job['outputKey']}")
            except Exception as e:
                print(f"Error deleting output {job['outputKey']}: {e}")
        
        # Update job status
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET cleanupTime = :cleanup_time',
            ExpressionAttributeValues={
                ':cleanup_time': int(datetime.utcnow().timestamp() * 1000)
            }
        )
        
        print(f"Cleanup completed for job {job_id}")
        
    except Exception as e:
        print(f"Error cleaning up job {job_id}: {e}")

def cleanup_expired_jobs():
    """Find and clean up jobs older than 24 hours"""
    try:
        table = dynamodb.Table(JOB_TABLE)
        
        # Scan for jobs older than 24 hours
        cutoff_time = int((datetime.utcnow() - timedelta(hours=24)).timestamp() * 1000)
        
        response = table.scan(
            FilterExpression='submitTime < :cutoff AND attribute_not_exists(cleanupTime)',
            ExpressionAttributeValues={':cutoff': cutoff_time}
        )
        
        for job in response['Items']:
            cleanup_job(job['jobId'])
        
        print(f"Scheduled cleanup processed {len(response['Items'])} expired jobs")
        
    except Exception as e:
        print(f"Error during scheduled cleanup: {e}")