import argparse, boto3

def main():
    p = argparse.ArgumentParser(description="Create a CPUUtilization alarm for an EC2 instance")
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--instance-id", required=True)
    p.add_argument("--sns-topic-arn", required=True)
    p.add_argument("--threshold", type=float, default=80.0)
    p.add_argument("--period", type=int, default=300)
    p.add_argument("--eval-periods", type=int, default=2)
    args = p.parse_args()

    cw = boto3.Session(profile_name=args.profile, region_name=args.region).client("cloudwatch")
    alarm_name = f"EC2-{args.instance_id}-HighCPU"
    cw.put_metric_alarm(
        AlarmName=alarm_name,
        ComparisonOperator="GreaterThanThreshold",
        EvaluationPeriods=args.eval_periods,
        MetricName="CPUUtilization",
        Namespace="AWS/EC2",
        Period=args.period,
        Statistic="Average",
        Threshold=args.threshold,
        ActionsEnabled=True,
        AlarmActions=[args.sns_topic_arn],
        Dimensions=[{"Name":"InstanceId","Value":args.instance_id}],
        TreatMissingData="notBreaching"
    )
    print(f"Created/updated alarm {alarm_name}")

if __name__ == "__main__":
    main()
