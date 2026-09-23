with open('main.py', 'r') as f:
    c = f.read()

c = c.replace(
    '("Instagram", "instagram", instagram_graph_connect.get_connection_status("local_test_user")["status"])',
    '("Instagram", "instagram-graph", instagram_graph_connect.get_connection_status("local_test_user")["status"])'
)

with open('main.py', 'w') as f:
    f.write(c)

print("Done")
