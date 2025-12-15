# AWS S3 Exfiltration Auto-Quarantine Playbook

**GuardDuty detects S3 exfiltration → Lambda copies objects to quarantine bucket → deletes originals → blocks public access. All in <20 seconds.**

Production-ready detection-as-code built by Yeury Perez, Founder & Lead Engineer at Silent Zero LLC.  
MITRE ATT&CK: T1567.002 (Exfiltration Over Web Service – S3 Download).

## Business Impact
- 90% of AWS breaches involve S3 data exfil.
- Default GuardDuty alerts only—no automated response.
- This playbook cuts MTTR from hours to seconds, preventing data loss.

Silent Zero deploys this for clients — fixed-fee $5,000–$7,500 (install + 3-month tuning retainer).  
DM "EXFIL" on LinkedIn/X for quote.

## Prerequisites
- AWS account with admin access (free tier eligible).
- GuardDuty enabled in any region zone.
- AWS CLI v2 configured (`aws configure` with IAM user keys, region ANY).
- IAM role for Lambda (least-privilege, created below).

## Step-by-Step Deployment (Copy-Paste CLI Commands)

```bash
# 1. Create buckets (replace UNIQ with unique string, e.g., yeury2025)
UNIQ="yeury-perez-silentzero-20251214"
aws s3api create-bucket --bucket victim-data-$UNIQ --region us-east-1
aws s3api create-bucket --bucket quarantine-$UNIQ --region us-east-1

# Block public on quarantine (secure default)
aws s3api put-public-access-block --bucket quarantine-$UNIQ --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Make victim public for demo exfil
aws s3api put-public-access-block --bucket victim-data-$UNIQ --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# 2. Upload dummy sensitive files (Phase 2 from lab)
for i in {1..25}; do
  head -c 4M /dev/urandom > sensitive-file-$i.bin
  aws s3 cp sensitive-file-$i.bin s3://victim-data-$UNIQ/
done
echo "<h1>Confidential Financial Data - Silent Zero Demo</h1><p>Exfil me if you can.</p>" > index.html
aws s3 cp index.html s3://victim-data-$UNIQ/

# 3. Deploy Lambda function (copy code from deploy/lambda_function.py)
# (Create role first in console if needed – see lab-report.pdf for details)

# 4. Wire EventBridge (full commands in lab-report.pdf)

# 5. Trigger exfil (manual sync loop or console test event)
for i in {1..30}; do
  mkdir -p ./exfil-run-$i
  aws s3 sync s3://victim-data-$UNIQ/ ./exfil-run-$i/
  sleep 1
done

# Wait 5–15 min → GuardDuty finding fires → objects quarantined + bucket locked.
