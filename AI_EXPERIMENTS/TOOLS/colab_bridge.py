import subprocess, threading, secrets, time, os

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
subprocess.Popen(["python3", "-m", "uvicorn", "bridge_app:app", "--host", "0.0.0.0", "--port", "8000"])
time.sleep(3)

if not os.path.exists("cloudflared"):
    subprocess.run("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared", shell=True)

proc = subprocess.Popen(["./cloudflared", "tunnel", "--url", "http://localhost:8000"], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
url = None
for line in proc.stderr:
    print(line, end="")
    if "trycloudflare.com" in line and url is None:
        import re
        m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if m:
            url = m.group(0)
            print("\n\n=== BRIDGE READY ===")
            print("URL:", url)
            print("TOKEN:", TOKEN)
            break
