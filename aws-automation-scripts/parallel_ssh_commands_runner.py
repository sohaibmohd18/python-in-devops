"""
parallel_ssh.py — run a command on many hosts via SSH with Paramiko

Examples:
  python parallel_ssh.py --hosts hosts.txt --user ec2-user --key ~/.ssh/id_rsa \
    --cmd "uname -a" --concurrency 20 --out report.json

  python parallel_ssh.py --hosts hosts.txt --user ubuntu --password 'secret' \
    --cmd "sudo -n systemctl restart nginx" --concurrency 10
"""
import argparse, json, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed

import paramiko

def connect(host, user, key_path=None, password=None, port=22, timeout=15, banner_timeout=15, look_for_keys=False):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        c.connect(
            hostname=host,
            username=user,
            port=port,
            pkey=paramiko.RSAKey.from_private_key_file(key_path) if key_path else None,
            password=password,
            allow_agent=False,
            look_for_keys=look_for_keys,
            timeout=timeout,
            banner_timeout=banner_timeout,
        )
        c.get_transport().set_keepalive(30)
        return c, None
    except Exception as e:
        return None, f"connect_error: {e}"

def run_command(client, cmd, timeout=120):
    try:
        _, stdout, stderr = client.exec_command(cmd, get_pty=True, timeout=timeout)
        out = stdout.read().decode(errors="replace")
        err = stderr.read().decode(errors="replace")
        rc = stdout.channel.recv_exit_status()
        return rc, out, err
    except Exception as e:
        return 255, "", f"exec_error: {e}"

def task(host, args):
    entry = {"host": host, "ok": False, "rc": None, "stdout": "", "stderr": "", "duration_s": None, "error": None}
    t0 = time.time()
    client, err = connect(host, args.user, args.key, args.password, args.port, args.timeout, args.banner_timeout, args.look_for_keys)
    if err:
        entry["error"] = err
        entry["duration_s"] = round(time.time() - t0, 3)
        return entry

    cmd = args.cmd
    if args.sudo and not cmd.strip().startswith("sudo"):
        # -n: non-interactive; command fails if sudo needs a password
        cmd = f"sudo -n bash -lc {json.dumps(cmd)}"
    elif args.login_shell:
        cmd = f"bash -lc {json.dumps(args.cmd)}"

    rc, out, err = run_command(client, cmd, args.exec_timeout)
    entry.update({"ok": rc == 0, "rc": rc, "stdout": out, "stderr": err, "duration_s": round(time.time() - t0, 3)})
    client.close()
    return entry

def main():
    p = argparse.ArgumentParser(description="Run a command on many hosts via SSH (Paramiko)")
    p.add_argument("--hosts", required=True, help="file with one host per line")
    p.add_argument("--user", required=True)
    p.add_argument("--key", help="private key path (PEM/OpenSSH)")
    p.add_argument("--password", help="password (discouraged; prefer keys)")
    p.add_argument("--port", type=int, default=22)
    p.add_argument("--cmd", required=True, help="command to run (quote it)")
    p.add_argument("--sudo", action="store_true", help="wrap command in sudo -n bash -lc")
    p.add_argument("--login-shell", action="store_true", help="run under bash -lc to load profile semantics")
    p.add_argument("--concurrency", type=int, default=20)
    p.add_argument("--timeout", type=int, default=15, help="TCP connect timeout")
    p.add_argument("--banner-timeout", type=int, default=15)
    p.add_argument("--exec-timeout", type=int, default=180)
    p.add_argument("--retries", type=int, default=0, help="retry attempts per host on failure")
    p.add_argument("--out", default="report.json")
    p.add_argument("--look-for-keys", action="store_true", help="allow agent/known keys if no --key")
    args = p.parse_args()

    with open(args.hosts) as f:
        hosts = [h.strip() for h in f if h.strip() and not h.strip().startswith("#")]

    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            fut_map = {ex.submit(task, h, args): (h, 0) for h in hosts}
            while fut_map:
                done, _ = as_completed(fut_map), None
                for fut in list(fut_map.keys()):
                    if not fut.done(): 
                        continue
                    h, attempt = fut_map.pop(fut)
                    res = fut.result()
                    if not res["ok"] and attempt < args.retries:
                        # schedule retry
                        fut_map[ex.submit(task, h, args)] = (h, attempt + 1)
                    else:
                        results.append(res)
    except KeyboardInterrupt:
        print("Interrupted by user.", file=sys.stderr)

    # write report
    with open(args.out, "w") as fp:
        json.dump({"command": args.cmd, "results": results}, fp, indent=2)
    # summary to stdout
    ok = sum(1 for r in results if r["ok"])
    print(f"completed: {ok}/{len(results)} ok; report -> {args.out}")

if __name__ == "__main__":
    main()
