import json
import boto3
import os
import zipfile
import io
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')

INPUT_BUCKET = os.environ['INPUT_BUCKET']
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
JOB_TABLE = os.environ['JOB_TABLE']
BEDROCK_MODEL_ID = os.environ['BEDROCK_MODEL_ID']
MAX_TOKENS = int(os.environ['MAX_TOKENS'])

def handler(event, context):
    try:
        job_id = event['jobId']
        input_key = event['inputKey']
        descriptor_key = event['descriptorKey']
        
        # Update job status to Running
        table = dynamodb.Table(JOB_TABLE)
        start_time = int(datetime.utcnow().timestamp() * 1000)
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, startTime = :start_time',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'Running',
                ':start_time': start_time
            }
        )
        
        # Retrieve files from S3
        archive_obj = s3.get_object(Bucket=INPUT_BUCKET, Key=input_key)
        descriptor_obj = s3.get_object(Bucket=INPUT_BUCKET, Key=descriptor_key)
        
        # Parse descriptor
        descriptor = json.loads(descriptor_obj['Body'].read().decode('utf-8'))
        
        # Extract source code from ZIP
        archive_data = archive_obj['Body'].read()
        source_files = extract_source_files(archive_data)
        
        # Build prompt
        prompt = build_prompt(source_files, descriptor)
        
        # Call Bedrock
        spec_text = call_bedrock(prompt)
        
        # Convert to Markdown and PDF
        markdown_content = format_as_markdown(spec_text, descriptor)
        pdf_content = convert_to_pdf(markdown_content)
        
        # Store outputs
        md_key = f"{job_id}/spec.md"
        pdf_key = f"{job_id}/spec.pdf"
        
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=md_key,
            Body=markdown_content,
            ContentType='text/markdown'
        )
        
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=pdf_key,
            Body=pdf_content,
            ContentType='application/pdf'
        )
        
        # Update job status to Succeeded
        end_time = int(datetime.utcnow().timestamp() * 1000)
        latency_ms = end_time - start_time
        
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, endTime = :end_time, outputKey = :output_key, latencyMs = :latency',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'Succeeded',
                ':end_time': end_time,
                ':output_key': pdf_key,
                ':latency': latency_ms
            }
        )
        
        return {
            'jobId': job_id,
            'status': 'Succeeded',
            'outputKey': pdf_key
        }
        
    except Exception as e:
        print(f"Error processing job {job_id}: {str(e)}")
        
        # Update job status to Failed
        table.update_item(
            Key={'jobId': job_id},
            UpdateExpression='SET #status = :status, errorMessage = :error',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'Failed',
                ':error': str(e)
            }
        )
        
        raise e

def extract_source_files(archive_data):
    """Extract up to 5 source files from ZIP, max 200 lines each"""
    source_files = []
    
    with zipfile.ZipFile(io.BytesIO(archive_data), 'r') as zip_file:
        for file_info in zip_file.filelist[:5]:  # Limit to 5 files
            if file_info.filename.endswith(('.cs', '.js', '.py', '.java')):
                try:
                    content = zip_file.read(file_info.filename).decode('utf-8')
                    lines = content.split('\n')[:200]  # Limit to 200 lines
                    source_files.append({
                        'filename': file_info.filename,
                        'content': '\n'.join(lines)
                    })
                except:
                    continue
    
    return source_files

def build_prompt(source_files, descriptor):
    """Build Bedrock prompt from source files and descriptor"""
    prompt = """You are a technical writer for a .NET e-commerce platform.
Given the following source code snippets and feature description, produce a Software Requirements Specification (SRS) that includes:

1. Overview
2. Functional Requirements (numbered list)
3. Non-Functional Requirements (performance, security)
4. Data Model (if applicable)
5. API Endpoints (if any)

Keep the total length ≤3000 words.

Feature Description:
"""
    
    prompt += json.dumps(descriptor, indent=2)
    prompt += "\n\nSource Code Files:\n"
    
    for file_info in source_files:
        prompt += f"\n--- {file_info['filename']} ---\n"
        prompt += file_info['content']
        prompt += "\n"
    
    prompt += "\n\nPlease generate a comprehensive SRS document based on the above information."
    
    return prompt

def call_bedrock(prompt):
    """Call Bedrock Claude model"""
    body = {
        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
        "max_tokens_to_sample": MAX_TOKENS,
        "temperature": 0.1,
        "top_p": 0.9,
    }
    
    response = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(body)
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['completion']

def format_as_markdown(spec_text, descriptor):
    """Format spec text as Markdown with front matter"""
    module_name = descriptor.get('moduleName', 'Unknown Module')
    version = descriptor.get('version', '1.0')
    
    markdown = f"""# Software Requirements Specification
**Module:** {module_name}  
**Version:** {version}  
**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}  

---

{spec_text}
"""
    
    return markdown

def convert_to_pdf(markdown_content):
    """Convert Markdown to PDF (simplified for PoC)"""
    # For PoC, return HTML-wrapped content as "PDF"
    html_content = f"""
    <html>
    <head>
        <title>Software Requirements Specification</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1, h2, h3 {{ color: #333; }}
            pre {{ background: #f5f5f5; padding: 10px; }}
        </style>
    </head>
    <body>
        <pre>{markdown_content}</pre>
    </body>
    </html>
    """
    
    return html_content.encode('utf-8')