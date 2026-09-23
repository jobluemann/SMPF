import os

env_path = r"C:\Users\RudiOosthuizen\smpf\.env"

with open(env_path, 'r') as f:
    content = f.read()

# Change Threads from http to https
if 'THREADS_CALLBACK_URL=http://' in content:
    content = content.replace(
        'THREADS_CALLBACK_URL=http://',
        'THREADS_CALLBACK_URL=https://'
    )
    print("Updated THREADS_CALLBACK_URL to HTTPS")
else:
    print("THREADS_CALLBACK_URL already HTTPS or not found")

with open(env_path, 'w') as f:
    f.write(content)
