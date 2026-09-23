with open('app/connectors/instagram_graph_connect.py', 'r') as f:
    c = f.read()

c = c.replace(
    'return meta_conn.get("access_token")',
    'return meta_conn.get("user_access_token") or meta_conn.get("access_token")'
)

with open('app/connectors/instagram_graph_connect.py', 'w') as f:
    f.write(c)

print("Done")
