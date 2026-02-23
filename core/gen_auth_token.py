
import hmac
import hashlib
import json
import urllib.parse

# 1. Setup Mock Secrets
BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" 
ADMIN_ID = 7695994098

# 2. Create Data Structure (Keys must be sorted a-z)
user_data = {
    "id": ADMIN_ID,
    "first_name": "Admin",
    "username": "admin",
    "last_name": "Test",
    "language_code": "en",
    "allows_write_to_pm": True
}

data_dict = {
    "auth_date": "1771409053",
    "query_id": "AAG_DEV",
    "user": json.dumps(user_data, separators=(',', ':'))
}

# 3. Create Data Check String
# Sort by key, join with \n, format 'key=value'
data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))

# 4. Sign
secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
data_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

# 5. Output ready-to-use string
# We need to URL encode the values for the frontend string, except 'hash' isn't part of data_check_string, it's appended.
# Actually, the frontend often sends the raw unparsed string (urlencoded).
# Let's construct the final queryString.
# query_id=...&user=...&auth_date=...&hash=...
# Standard format: key=value&key=value... with keys sorted? Telegram doesn't strictly require sorted keys in the final string, 
# but the hash calculation DOES require sorted keys. 
# The browser usually sends them however.
# Let's just urlencode the components.

final_params = data_dict.copy()
final_params['hash'] = data_hash

final_string = urllib.parse.urlencode(final_params)

with open("temp_auth_token.txt", "w") as f:
    f.write(final_string)

print("Token written to temp_auth_token.txt")
print(f"BOT_TOKEN={BOT_TOKEN}")
print(f"ADMIN_ID={ADMIN_ID}")
