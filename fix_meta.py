with open('app/connectors/meta_connect.py', 'r') as f:
    lines = f.readlines()

# Find and remove lines 33-35 (0-indexed: 32-34) which contain the old comment + old SCOPES
# Line 29-32 is the new comment + new SCOPES, line 33-35 is the old leftover
output = []
for i, line in enumerate(lines):
    # Skip lines 33-35 (1-indexed) which contain old comment and old SCOPES
    if i >= 32 and i <= 34:  # 0-indexed lines 32, 33, 34
        # Check if this is the old SCOPES line with instagram_business_basic
        if 'instagram_business_basic' in line:
            continue
        # Check if this is the old comment
        if 'instagram_business_basic is rejected' in line or 'If instagram_business_basic' in line:
            continue
    output.append(line)

with open('app/connectors/meta_connect.py', 'w') as f:
    f.writelines(output)

print("Done")
