import urllib.request
import json
import urllib.error

# First register mapping
reg_url = "http://localhost:8000/auth/student/register-mapping"
data = json.dumps({
    "username": "testuser",
    "password": "Password@123",
    "register_number": "212222240047"
}).encode("utf-8")

req = urllib.request.Request(reg_url, data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as response:
        print("Registration Response:")
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error (Registration): {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Error (Registration): {e}")

# Then test login
url = "http://localhost:8000/auth/student/login"
req2 = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req2) as response:
        print("Login Response:")
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error (Login): {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Error (Login): {e}")
