import requests

# Try alternative endpoints to find linked Instagram
page_token = "EAAM9ITIv6GEBSUixmy5cLK3FVRkQRa8A4NMjkFYwqp98m1YcAY6cvZA6C65s1lGA3hZCHoULVEl552TwkKCUCTC9dLuKsv1u7YruOckjKkSAmWeAEkfK2ZACNmoRAEhJjM1xgbG9UTJ5JVPnw7dJL9ba59lgWT8k9gZCQab5rVnzNmwjDrXpVyOvMMd7kIviaxwCWggZD"
page_id = "101916918609027"
GRAPH_BASE = "https://graph.facebook.com/v21.0"

print("=== Try connected_instagram_account endpoint ===")
r = requests.get(f"{GRAPH_BASE}/{page_id}", params={
    "access_token": page_token,
    "fields": "connected_instagram_account,instagram_business_account"
})
print(f"Status: {r.status_code}")
print(r.json())
