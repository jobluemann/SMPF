import re

with open(r'C:/Users/RudiOosthuizen/smpf/app/connectors/x_connect.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the duplicate SCOPES block (lines 40-42)
pattern = r'SCOPES = \["tweet\.read", "users\.read", "offline\.access", "tweet\.write"\]\r?\n# access token .+?\r?\n# constantly\. tweet\.read/users\.read are the minimum for reading identity\.\r?\nSCOPES = \["tweet\.read", "users\.read", "offline\.access"\]'

replacement = 'SCOPES = ["tweet.read", "users.read", "offline.access", "tweet.write"]'

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print('ERROR: Pattern not found - no changes made')
    print('--- First 100 chars after SCOPES line 1 ---')
    idx = content.find('SCOPES =')
    if idx != -1:
        print(repr(content[idx:idx+200]))
else:
    with open(r'C:/Users/RudiOosthuizen/smpf/app/connectors/x_connect.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS: Fixed SCOPES in x_connect.py')
