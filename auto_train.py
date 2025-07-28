import os
import boto3
import json
import datetime
import subprocess
import requests

# === AWS Credentials from Environment ===
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "proof-logger"

# === Render Credentials from Environment ===
RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")

# === Filenames and S3 Keys ===
SIGNAL_FILE = "signal_log.json"
CLICK_FILE = "click_log.json"
S3_SIGNAL_KEY = "logs/signal_log.json"
S3_CLICK_KEY = "logs/click_log.json"

# === Connect to S3 ===
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# === Download Logs from S3 ===
def download_log(s3_key, local_file):
    try:
        s3.download_file(S3_BUCKET_NAME, s3_key, local_file)
        print(f"✅ Downloaded {s3_key} → {local_file}")
    except Exception as e:
        print(f"❌ Error downloading {s3_key}: {e}")

# === Train ProofModel ===
def run_training():
    print("\n🔄 Generating dataset...")
    subprocess.run(["python", "generate_training_dataset.py"], check=True)

    print("\n🧠 Training ProofModel v2...")
    subprocess.run(["python", "training_loop.py"], check=True)

# === Upload Model to S3 ===
def upload_model():
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    versioned_key = f"models/proofmodel_v2_{timestamp}.pth"
    latest_key = "models/latest_proofmodel_v2.pth"
    try:
        s3.upload_file("proofmodel_v2.pth", S3_BUCKET_NAME, versioned_key)
        s3.upload_file("proofmodel_v2.pth", S3_BUCKET_NAME, latest_key)
        print(f"✅ Uploaded model to S3:\n  - {versioned_key}\n  - {latest_key}")
    except Exception as e:
        print(f"❌ Error uploading model: {e}")

# === Trigger Render Redeploy ===
def trigger_render_redeploy():
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        print("⚠️ Skipping redeploy (Render credentials not set)")
        return

    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys"
    headers = {"Authorization": f"Bearer {RENDER_API_KEY}"}
    response = requests.post(url, headers=headers)

    if response.status_code == 201:
        print("🚀 Triggered redeploy on Render!")
    else:
        print(f"❌ Failed to trigger redeploy: {response.text}")

# === MAIN ===
if __name__ == "__main__":
    download_log(S3_SIGNAL_KEY, SIGNAL_FILE)
    download_log(S3_CLICK_KEY, CLICK_FILE)
    run_training()
    upload_model()
    trigger_render_redeploy()
