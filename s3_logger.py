import boto3
import json
import datetime

# === 🔐 Replace these with your actual AWS credentials ===
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "proof-logger"

# === S3 client setup ===
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# === Upload function ===
def upload_json_to_s3(data, key_prefix="logs/"):
    """
    Uploads a JSON object to S3 under a timestamped filename.
    """
    timestamp = datetime.datetime.utcnow().isoformat().replace(":", "-")
    key = f"{key_prefix}{timestamp}.json"

    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=json.dumps(data, indent=2),
            ContentType="application/json"
        )
        print(f"✅ Uploaded log to S3: {key}")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")