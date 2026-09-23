import uvicorn, threading, time, urllib.request
from main import app

def run():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(3)
resp = urllib.request.urlopen("http://127.0.0.1:8001/").read().decode()
print(resp[:800])
print("\n--- STATIC FILE TEST ---")
resp2 = urllib.request.urlopen("http://127.0.0.1:8001/static/style.css").read().decode()[:200]
print(resp2)
