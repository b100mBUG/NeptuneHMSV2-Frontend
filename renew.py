import hashlib
from datetime import datetime, timedelta

SECRET_KEY = "DROSOPHILLAMELANOGASTER"
user_name = input("Enter Username: ")
def generate_license(username: str) -> str:
    expiry_time = datetime.utcnow() + timedelta(days= 30)
    expiry_str = expiry_time.strftime("%Y-%m-%d %H:%M:%S")
    data = f"{username}-{expiry_str}-{SECRET_KEY}"
    checksum = hashlib.sha256(data.encode()).hexdigest()[:10].upper()
    license_key = f"{username}|{expiry_str}|{checksum}"
    print(license_key)
generate_license(user_name.upper())


