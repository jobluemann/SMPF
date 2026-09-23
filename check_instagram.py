import app.connectors.instagram_connect as ic
print("Instagram Auth URL:")
print(ic.get_authorize_url("test_state_123"))
print()
print("Redirect URI used:", ic._redirect_uri)
print("Scopes:", ic.SCOPES)
