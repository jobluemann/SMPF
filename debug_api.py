import requests
import json

GRAPH_BASE = "https://graph.facebook.com/v21.0"

# User access token from meta_connections.json
user_token = "EAAM9ITIv6GEBSaLZBOwJa5yMUw0kd6S8worGUmV9rwjKsWOIYo3hC6u8kHCE4Ggiod7FErFYVJxCOg6ZAfVOth6XX0vYDTOlMmZAR1qMmACKAZAsrCLMYI8YVjc2w0bWaWZBY9NuV7VDK1BathrDy2dMZCAMyDjPLqdckQdp3GFdZBS3eAKZAzfsjHoRHai5"

# Page access token
page_token = "EAAM9ITIv6GEBSUixmy5cLK3FVRkQRa8A4NMjkFYwqp98m1YcAY6cvZA6C65s1lGA3hZCHoULVEl552TwkKCUCTC9dLuKsv1u7YruOckjKkSAmWeAEkfK2ZACNmoRAEhJjM1xgbG9UTJ5JVPnw7dJL9ba59lgWT8k9gZCQab5rVnzNmwjDrXpVyOvMMd7kIviaxwCWggZD"

print("=== Test 1: User token with instagram_business_account field ===")
r = requests.get(f"{GRAPH_BASE}/me/accounts", params={
    "access_token": user_token,
    "fields": "id,name,instagram_business_account"
})
print(f"Status: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2)[:1000])

print("\n=== Test 2: Page token with instagram_business_account field ===")
r = requests.get(f"{GRAPH_BASE}/101916918609027", params={
    "access_token": page_token,
    "fields": "id,name,instagram_business_account"
})
print(f"Status: {r.status_code}")
data = r.json()
print(json.dumps(data, indent=2)[:1000])

print("\n=== Test 3: Check token permissions ===")
r = requests.get(f"{GRAPH_BASE}/debug_token", params={
    "input_token": user_token,
    "access_token": user_token
})
print(f"Status: {r.status_code}")
data = r.json()
perms = data.get("data", {}).get("scopes", [])
print("Permissions:", perms)
