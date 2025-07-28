import os
import boto3
import json
import datetime
import subprocess

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "proof-logger"

# Local filenames
SIGNAL_FILE = "signal_log.json"
CLICK_FILE = "click_log.json"

# S3 keys (update if needed)
S3_SIGNAL_KEY = "logs/signal_log.json"
S3_CLICK_KEY = "logs/click_log.json"

# === 1. Connect to S3 ===
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# === 2. Download Logs ===
def download_log(s3_key, local_file):
    try:
        s3.download_file(S3_BUCKET_NAME, s3_key, local_file)
        print(f"✅ Downloaded {s3_key} → {local_file}")
    except Exception as e:
        print(f"❌ Error downloading {s3_key}: {e}")

# === 3. Train Model ===
def run_training():
    print("\n🔄 Generating dataset...")
    subprocess.run(["python", "generate_training_dataset.py"], check=True)

    print("\n🧠 Training ProofModel v2...")
    subprocess.run(["python", "training_loop.py"], check=True)

# === 4. Upload Updated Model to S3 ===
def upload_model():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    s3_key = f"models/proofmodel_v2_{timestamp}.pth"
    try:
        s3.upload_file("proofmodel_v2.pth", S3_BUCKET_NAME, s3_key)
        print(f"✅ Uploaded model to S3: {s3_key}")
    except Exception as e:
        print(f"❌ Error uploading model: {e}")

# === 5. Main ===
if __name__ == "__main__":
    download_log(S3_SIGNAL_KEY, SIGNAL_FILE)
    download_log(S3_CLICK_KEY, CLICK_FILE)
    run_training()
    upload_model()