import os
from app.config import DATA_DIR

print("DATA_DIR:", DATA_DIR)
print("Exists:", os.path.exists(DATA_DIR))
if os.path.exists(DATA_DIR):
    print("Contents:", os.listdir(DATA_DIR))
