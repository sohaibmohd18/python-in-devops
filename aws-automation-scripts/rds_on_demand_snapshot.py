import argparse, boto3, datetime, time

def main():
    p = argparse.ArgumentParser(description="RDS snapshot + prune")
    p.add_argument("--profile", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--db-id", required=True, help="DBInstanceIdentifier")
    p.add_argument("--retain", type=int, default=7)
    args = p.parse_args()

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    rds = session.client("rds")
    ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snap_id = f"{args.db_id}-manual-{ts}"

    print(f"Creating snapshot {snap_id}")
    rds.create_db_snapshot(DBInstanceIdentifier=args.db_id, DBSnapshotIdentifier=snap_id)

    waiter = rds.get_waiter("db_snapshot_available")
    waiter.wait(DBSnapshotIdentifier=snap_id)
    print("Snapshot available.")

    # Prune old
    snaps = rds.describe_db_snapshots(DBInstanceIdentifier=args.db_id, SnapshotType="manual")["DBSnapshots"]
    snaps.sort(key=lambda s: s["SnapshotCreateTime"], reverse=True)
    for s in snaps[args.retain:]:
        sid = s["DBSnapshotIdentifier"]
        print(f"Deleting old snapshot {sid}")
        rds.delete_db_snapshot(DBSnapshotIdentifier=sid)

if __name__ == "__main__":
    main()
