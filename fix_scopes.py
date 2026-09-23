import re

f = open(r'C:/Users/RudiOosthuizen/smpf/app/connectors/x_connect.py', 'r')
s = f.read()
f.close()

# Remove the duplicate SCOPES assignment (lines 40-42)
old = '''SCOPES = ["tweet.read", "users.read", "offline.access", "tweet.write"]
# access token — otherwise the client would have to reconnect
# constantly. tweet.read/users.read are the minimum for reading identity.
SCOPES = ["tweet.read", "users.read", "offline.access"]'''

new = 'SCOPES = ["tweet.read", "users.read", "offline.access", "tweet.write"]'

s = s.replace(old, new)

f = open(r'C:/Users/RudiOosthuizen/smpf/app/connectors/x_connect.py', 'w')
f.write(s)
f.close()

print('Fixed SCOPES in x_connect.py')
