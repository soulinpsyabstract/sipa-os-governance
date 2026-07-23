import subprocess, secrets, time, os, re

TOKEN = secrets.token_hex(16)
os.environ["BRIDGE_TOKEN"] = TOKEN

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

subprocess.run("pip install -q fastapi uvicorn", shell=True)

# Redirect ALL child output to log files (not pipes) so nothing can block on a full buffer,
# and so this launcher process can exit immediately instead of holding the cell open forever.
uv_log = open("uvicorn.log", "w")
subprocess.Popen(
    ["python3", "-m", "uvicorn", "bridge_app:app", "--host", "0.0.0.0", "--port", "8000"],
    stdout=uv_log, stderr=uv_log, start_new_session=True,
)
time.sleep(3)

if not os.path.exists("cloudflared"):
    subprocess.run(
        "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared",
        shell=True,
    )

cf_log = open("cloudflared.log", "w")
subprocess.Popen(
    ["./cloudflared", "tunnel", "--url", "http://localhost:8000"],
    stdout=cf_log, stderr=cf_log, start_new_session=True,
)

url = None
for _ in range(30):
    time.sleep(1)
    if os.path.exists("cloudflared.log"):
        content = open("cloudflared.log").read()
        m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
        if m:
            url = m.group(0)
            break

print("=== BRIDGE READY ===")
print("URL:", url)
print("TOKEN:", TOKEN)
print("(this cell has now exited - the server keeps running in the background via start_new_session)")
