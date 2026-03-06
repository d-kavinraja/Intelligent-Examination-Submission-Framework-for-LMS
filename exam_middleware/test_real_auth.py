import urllib.request
import json
import urllib.error

# Student Credentials
USERNAME = "22007928"
PASSWORD = "Kavin1612!"
REGISTER_NUMBER = "212222240047"

# Test login (Mapping should already exist based on check_state.py)
url = "http://localhost:8000/auth/student/login"
data = json.dumps({
    "username": USERNAME,
    "password": PASSWORD,
    "register_number": REGISTER_NUMBER
}).encode("utf-8")

req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

print(f"Testing login for {USERNAME}...")
try:
    with urllib.request.urlopen(req) as response:
        print("Login Response:")
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error (Login): {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Error (Login): {e}")
