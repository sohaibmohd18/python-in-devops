import argparse, boto3, botocore

def main():
    p = argparse.ArgumentParser(description="Start/stop EC2 instances by tag")
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--tag-key", required=True)
    p.add_argument("--tag-value", required=True)
    p.add_argument("--action", choices=["start", "stop"], required=True)
    args = p.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    ec2 = session.client("ec2")
    paginator = ec2.get_paginator("describe_instances")

    filters = [
        {"Name": f"tag:{args.tag_key}", "Values": [args.tag_value]},
        {"Name": "instance-state-name", "Values": ["stopped" if args.action=="start" else "running"]}
    ]
    instance_ids = []
    for page in paginator.paginate(Filters=filters):
        for r in page["Reservations"]:
            for i in r["Instances"]:
                instance_ids.append(i["InstanceId"])

    if not instance_ids:
        print("No matching instances.")
        return

    print(f"{args.action.title()}ing: {', '.join(instance_ids)}")
    if args.action == "start":
        ec2.start_instances(InstanceIds=instance_ids)
    else:
        ec2.stop_instances(InstanceIds=instance_ids)

if __name__ == "__main__":
    main()
