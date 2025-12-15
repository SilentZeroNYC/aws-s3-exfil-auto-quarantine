import json
import boto3

s3 = boto3.client('s3')
quarantine_bucket = "quarantine-yeury-perez-silentzero-20251213"  # <<< UPDATE TO YOUR EXACT QUARANTINE BUCKET NAME

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, default=str))
    
    # Handle direct EventBridge from GuardDuty (primary path)
    if 'detail' in event:
        finding = event['detail']
    # Handle SNS wrapper (fallback for other integrations)
    elif 'Records' in event and len(event['Records']) > 0:
        message = json.loads(event['Records'][0]['Sns']['Message'])
        finding = message['detail']
    else:
        print("Unknown event format – no action taken")
        return {'statusCode': 400, 'body': 'Invalid event'}
    
    if 'Exfiltration:S3' in finding.get('title', ''):
        bucket = finding['resource']['s3Bucket']['name']
        objects = finding['service']['additionalInfo'].get('objects', [])
        
        for obj in objects:
            key = obj['key']
            copy_source = {'Bucket': bucket, 'Key': key}
            print(f"Quarantining {key} from {bucket}")
            s3.copy_object(CopySource=copy_source, Bucket=quarantine_bucket, Key=key)
            s3.delete_object(Bucket=bucket, Key=key)
        
        print("Blocking public access on victim bucket")
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print("Quarantine and lockdown complete")
    
    return {'statusCode': 200}
