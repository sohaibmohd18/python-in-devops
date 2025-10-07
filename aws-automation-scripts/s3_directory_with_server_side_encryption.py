import argparse, boto3, os
from botocore.config import Config

def upload_dir(s3, bucket, prefix, local_dir):
    for root, _, files in os.walk(local_dir):
        for f in files:
            full_path = os.path.join(root, f)
            key = f"{prefix}/{os.path.relpath(full_path, start=local_dir)}".replace("\\","/")
            print(f"Uploading {full_path} -> s3://{bucket}/{key}")
            s3.upload_file(full_path, bucket, key, ExtraArgs={"ServerSideEncryption":"AES256"})

def set_lifecycle(s3c, bucket, days_current=30, days_noncurrent=30):
    rule = {
        "Rules":[
            {
                "ID":"expire-current",
                "Status":"Enabled",
                "Filter":{"Prefix":""},
                "Expiration":{"Days":days_current},
                "NoncurrentVersionExpiration":{"NoncurrentDays":days_noncurrent}
            }
        ]
    }
    s3c.put_bucket_lifecycle_configuration(Bucket=bucket, LifecycleConfiguration=rule)

def main():
    p = argparse.ArgumentParser(description="Upload folder to S3 with SSE and lifecycle")
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--bucket", required=True)
    p.add_argument("--prefix", default="")
    p.add_argument("--path", required=True)
    p.add_argument("--set-lifecycle", action="store_true")
    args = p.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    s3 = session.client("s3", config=Config(retries={"max_attempts":10,"mode":"standard"}))

    upload_dir(s3, args.bucket, args.prefix.strip("/"), args.path)

    if args.set_lifecycle:
        set_lifecycle(s3, args.bucket)
        print("Lifecycle configuration applied.")

if __name__ == "__main__":
    main()
