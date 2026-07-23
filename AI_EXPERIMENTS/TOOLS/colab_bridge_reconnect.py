import subprocess, os, time, re

# Use when the previous cloudflared quick tunnel died (Cloudflare error 1033) but the
# uvicorn bridge server on port 8000 is still alive - just opens a fresh tunnel to it,
# without re-installing or restarting anything else. TOKEN is unchanged from before.

if not os.path.exists("cloudflared"):
    subprocess.run(
        "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared",
        shell=True,
    )

cf_log = open("cloudflared2.log", "w")
subprocess.Popen(
    ["./cloudflared", "tunnel", "--url", "http://localhost:8000"],
    stdout=cf_log, stderr=cf_log, start_new_session=True,
)

url = None
for _ in range(30):
    time.sleep(1)
    if os.path.exists("cloudflared2.log"):
        content = open("cloudflared2.log").read()
        m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
        if m:
            url = m.group(0)
            break

print("=== RECONNECTED ===")
print("NEW URL:", url)
print("(TOKEN is unchanged from the original bridge run)")
