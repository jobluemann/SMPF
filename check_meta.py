import json

with open('data/meta_connections.json') as f:
    d = json.load(f)

print(json.dumps(d, indent=2, default=str))
