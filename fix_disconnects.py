with open('main.py', 'r') as f:
    c = f.read()

# Replace all disconnect routes that return raw JSON to redirect instead
# Pattern: return xxxx_connect.disconnect("local_test_user")
# Replace with: xxxx_connect.disconnect("local_test_user"); return RedirectResponse("/dashboard")

import re

# Find all disconnect route functions and update them
def fix_disconnect_route(match):
    indent = match.group(1)
    connector = match.group(2)
    return f'{indent}{connector}.disconnect("local_test_user")\n{indent}return RedirectResponse("/dashboard")'

# Match pattern: def xxx_disconnect():\n    return xxx.disconnect("local_test_user")
c = re.sub(
    r'(def (\w+)_disconnect\(\):\n)(    )return \w+\.disconnect\("local_test_user"\)',
    lambda m: f'{m.group(1)}{m.group(3)}{m.group(2)}_connect.disconnect("local_test_user")\n{m.group(3)}return RedirectResponse("/dashboard")',
    c
)

# Handle special cases where variable name doesn't match pattern
# Instagram direct disconnect
# Instagram Graph disconnect
# Google Drive disconnect
c = c.replace(
    '    return instagram_connect.disconnect("local_test_user")',
    '    instagram_connect.disconnect("local_test_user")\n    return RedirectResponse("/dashboard")'
)
c = c.replace(
    '    return instagram_graph_connect.disconnect("local_test_user")',
    '    instagram_graph_connect.disconnect("local_test_user")\n    return RedirectResponse("/dashboard")'
)
c = c.replace(
    '    return google_drive.disconnect("local_test_user")',
    '    google_drive.disconnect("local_test_user")\n    return RedirectResponse("/dashboard")'
)

with open('main.py', 'w') as f:
    f.write(c)

print("Done")
