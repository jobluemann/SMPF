import os

env_path = r"C:\Users\RudiOosthuizen\smpf\.env"

with open(env_path, 'r') as f:
    content = f.read()

# Check what callback URLs are missing
needed = {
    'META_CALLBACK_URL': 'http://localhost:8000/connectors/meta/callback',
    'THREADS_CALLBACK_URL': 'http://localhost:8000/connectors/threads/callback',
    'YOUTUBE_CALLBACK_URL': 'http://localhost:8000/connectors/youtube/callback',
    'REDDIT_CALLBACK_URL': 'http://localhost:8000/connectors/reddit/callback',
    'MINDS_CALLBACK_URL': 'http://localhost:8000/connectors/minds/callback',
    'VK_CALLBACK_URL': 'http://localhost:8000/connectors/vk/callback',
    'GOOGLE_CALLBACK_URL': 'http://localhost:8000/connectors/youtube/callback',
    'GOOGLE_DRIVE_CALLBACK_URL': 'http://localhost:8000/connectors/google_drive/callback',
}

added = []
for key, value in needed.items():
    if key not in content:
        content += f"\n{key}={value}"
        added.append(key)

with open(env_path, 'w') as f:
    f.write(content)

if added:
    print(f"Added {len(added)} missing callback URLs:")
    for a in added:
        print(f"  - {a}")
else:
    print("All callback URLs already present.")
