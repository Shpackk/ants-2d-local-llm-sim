import json
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:1337/v1"
API_KEY = "jan"

request = Request(
    f"{BASE_URL}/models",
    headers={"Authorization": f"Bearer {API_KEY}"},
    method="GET",
)

with urlopen(request, timeout=8.0) as response:
    print(response.status)
    print(json.dumps(json.loads(response.read().decode("utf-8")), indent=2))
