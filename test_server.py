import uvicorn, threading, time, urllib.request
from main import app

def run():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

t = threading.Thread(target=run, daemon=True)
t.start()
time.sleep(3)
resp = urllib.request.urlopen("http://127.0.0.1:8000/").read().decode()
print(resp[:800])
