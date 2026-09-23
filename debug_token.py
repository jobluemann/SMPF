from app.connectors import meta_connect, instagram_graph_connect

print("=== Debug: _get_meta_token ===")
token = instagram_graph_connect._get_meta_token("local_test_user")
print(f"Token returned: {token is not None}")
if token:
    print(f"Token length: {len(token)}")
else:
    print("Token is None/empty")

print("\n=== Raw meta connections ===")
raw = meta_connect._load_connections()
print(f"Keys: {list(raw.keys())}")
if "local_test_user" in raw:
    conn = raw["local_test_user"]
    print(f"Has user_access_token: {'user_access_token' in conn}")
    print(f"Has access_token: {'access_token' in conn}")
    print(f"Status: {conn.get('status')}")
