import json
import os

os.makedirs("data", exist_ok=True)

data = {
    "local_test_user": {
        "platform": "x",
        "access_token": "R2NHaG1oOTdJR0h5SVpIQnVDY19UU3dMRU1CXzhfY0tEUElyWkVBLV93SG1VOjE3ODg3MDk1MzY1NTc6MToxOmF0OjE",
        "refresh_token": "MlkzUHBBUXV1MXd3THRLbTB5c2NSdXg5MTBaeWlVOWp4bVJtOUtfOGtqUzRfOjE3ODg3MDk1MzY1NTc6MTowOnJ0OjE",
        "expires_in_seconds": 7200,
        "identity": {
            "user_id": "1183789584511049728",
            "username": "jobluemann",
            "name": "jobluemann"
        },
        "status": "connected"
    }
}

with open("data/x_connections.json", "w") as f:
    json.dump(data, f, indent=2)

print("OK")
