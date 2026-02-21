import hmac
import hashlib
import json
from urllib.parse import parse_qsl

# Values from .env and ProtocolDashboard.tsx
BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
ADMIN_ID = "123456789"
init_data = "auth_date=1771409053&query_id=AAG_DEV&user=%7B%22id%22%3A+123456789%2C+%22first_name%22%3A+%22Admin%22%2C+%22username%22%3A+%22admin%22%2C+%22last_name%22%3A+%22Test%22%2C+%22language_code%22%3A+%22en%22%2C+%22allows_write_to_pm%22%3A+true%7D&hash=95f52384f51459165582dd59d7bb9e32b5cf449cb1a08a3ab3350fb618d01f2b"

def verify():
    parsed_data = dict(parse_qsl(init_data))
    if "hash" not in parsed_data:
        print("Error: hash missing from parsed data")
        return
    
    input_hash = parsed_data.pop("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
    
    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    print(f"Input Hash:      {input_hash}")
    print(f"Calculated Hash: {calculated_hash}")
    
    if calculated_hash == input_hash:
        print("Signature: VALID")
    else:
        print("Signature: INVALID")

    user_data = json.loads(parsed_data.get("user", "{}"))
    user_id = str(user_data.get("id"))
    print(f"User ID: {user_id}")
    print(f"Admin ID: {ADMIN_ID}")
    
    if user_id == ADMIN_ID:
        print("ID Locking: MATCH")
    else:
        print("ID Locking: MISMATCH")

if __name__ == "__main__":
    verify()
