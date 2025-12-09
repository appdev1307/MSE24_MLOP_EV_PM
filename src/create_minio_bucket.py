import boto3
from botocore.client import Config

def create_bucket(bucket_name="mlflow-artifacts"):
    s3 = boto3.client(
        "s3",
        endpoint_url="http://localhost:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        config=Config(signature_version="s3v4"),
        region_name="us-east-1"
    )
    existing = [bucket['Name'] for bucket in s3.list_buckets().get('Buckets', [])]
    if bucket_name not in existing:
        s3.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created")
    else:
        print(f"Bucket '{bucket_name}' already exists")

if __name__ == "__main__":
    create_bucket()
