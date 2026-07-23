import subprocess, os, time, re

# Use when the previous connection died. Handles two cases:
# 1. uvicorn bridge server is still alive, just the tunnel died (Cloudflare 1033) -> only reopens the tunnel
# 2. uvicorn itself crashed (Cloudflare 502 bad gateway) -> restarts uvicorn from the existing bridge_app.py, then opens a tunnel
# TOKEN is read from the existing bridge_app.py's environment reference - since bridge_app.py itself
# reads os.environ["BRIDGE_TOKEN"] at import time, we must re-export the same token used originally.
# If you don't remember it, this script prints a NEW token - use that one going forward instead.

port_check = subprocess.run("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/exec -X POST -d '{}' 2>/dev/null", shell=True, capture_output=True, text=True)
server_alive = port_check.stdout.strip() not in ("", "000")

if not server_alive:
    print("uvicorn not responding locally - restarting it")
    import secrets
    TOKEN = secrets.token_hex(16)
    os.environ["BRIDGE_TOKEN"] = TOKEN
    if not os.path.exists("bridge_app.py"):
        app_code = '''
import subprocess, os
from fastapi import FastAPI, Header, HTTPException
app = FastAPI()
TOKEN = os.environ["BRIDGE_TOKEN"]

@app.post("/exec")
async def exec_code(body: dict, authorization: str = Header(None)):
    if authorization != f"Bearer {TOKEN}":
        raise HTTPException(401)
    cmd = body["cmd"]
    timeout = body.get("timeout", 1200)
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout[-15000:], "stderr": r.stderr[-15000:], "returncode": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TIMEOUT", "returncode": -1}
'''
        with open("bridge_app.py", "w") as f:
            f.write(app_code)
    uv_log = open("uvicorn2.log", "w")
    subprocess.Popen(
        ["python3", "-m", "uvicorn", "bridge_app:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=uv_log, stderr=uv_log, start_new_session=True,
        env={**os.environ, "BRIDGE_TOKEN": TOKEN},
    )
    time.sleep(4)
    print("NEW TOKEN (bridge_app.py restarted, old token no longer valid):", TOKEN)
else:
    print("uvicorn still alive locally - reusing existing TOKEN, only reopening the tunnel")

if not os.path.exists("cloudflared"):
    subprocess.run(
        "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared",
        shell=True,
    )

cf_log = open(f"cloudflared_{int(time.time())}.log", "w")
subprocess.Popen(
    ["./cloudflared", "tunnel", "--url", "http://localhost:8000"],
    stdout=cf_log, stderr=cf_log, start_new_session=True,
)

url = None
for _ in range(30):
    time.sleep(1)
    content = open(cf_log.name).read()
    m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
    if m:
        url = m.group(0)
        break

print("=== RECONNECTED ===")
print("NEW URL:", url)
