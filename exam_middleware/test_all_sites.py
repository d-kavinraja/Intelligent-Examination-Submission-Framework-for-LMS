import urllib.request
import json
import urllib.error

# Student Credentials
USERNAME = "22007928"
PASSWORD = "Kavin1612!"

SITES = [
    "https://lms2.ai.saveetha.in",
    "https://lms2.cse.saveetha.in",
    "https://lms2.ece.saveetha.in",
    "https://lms2.eee.saveetha.in",
    "http://lms.ai.saveetha.in"
]

for site in SITES:
    print(f"Testing {site}...")
    url = f"{site}/login/token.php?username={USERNAME}&password={PASSWORD}&service=moodle_mobile_app"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            if "token" in res_data:
                print(f"SUCCESS on {site}!")
                print(res_data)
            else:
                print(f"FAILED on {site}: {res_data}")
    except Exception as e:
        print(f"ERROR on {site}: {e}")
    print("-" * 20)
