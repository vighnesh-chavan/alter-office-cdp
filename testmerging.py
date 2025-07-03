import requests
import json

BASE_URL = "http://localhost:8000/api"


def print_pretty(label, response):
    print(f"{label} | Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


# ---------- Test 1: Ingest Initial User ----------


def test_identity_initial_ingest():
    payload = {
        "data": [
            {
                "cookie": "cookie123",
                "email": "testuser@example.com",
                "phone_number": "+1000000000",
                "location": {"state": "Texas", "country": "USA", "city": "Dallas"},
                "demographics": {
                    "age": 28,
                    "gender": "Male",
                    "income": "$70,000-$89,999",
                    "education": "Bachelor's",
                },
                "interests": ["music", "hiking"],
            }
        ]
    }
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    print_pretty("Initial Ingest", response)


# ---------- Test 2: Same Cookie, Different Email (should merge?) ----------


def test_same_cookie_different_email():
    payload = {
        "data": [
            {
                "cookie": "cookie123",  # same cookie as before
                "email": "newemail@example.com",  # new email
                "phone_number": "+1000000001",
                "location": {"state": "Texas", "country": "USA", "city": "Dallas"},
                "demographics": {
                    "age": 28,
                    "gender": "Male",
                    "income": "$70,000-$89,999",
                    "education": "Bachelor's",
                },
                "interests": ["music", "travel"],
            }
        ]
    }
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    print_pretty("Same Cookie, Different Email Ingest", response)

    # Check if both emails map to the same user
    response1 = requests.get(f"{BASE_URL}/user", params={"cookie": "cookie123"})
    print_pretty("Fetch by Cookie", response1)

    response2 = requests.get(
        f"{BASE_URL}/user", params={"email": "newemail@example.com"}
    )
    print_pretty("Fetch by New Email", response2)


# ---------- Test 3: Same Email, Different Cookie (should merge?) ----------


def test_same_email_different_cookie():
    payload = {
        "data": [
            {
                "cookie": "cookie999",  # new cookie
                "email": "testuser@example.com",  # existing email
                "phone_number": "+1000000002",
                "location": {"state": "Texas", "country": "USA", "city": "Dallas"},
                "demographics": {
                    "age": 28,
                    "gender": "Male",
                    "income": "$70,000-$89,999",
                    "education": "Bachelor's",
                },
                "interests": ["reading"],
            }
        ]
    }
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    print_pretty("Same Email, Different Cookie Ingest", response)

    response1 = requests.get(
        f"{BASE_URL}/user", params={"email": "testuser@example.com"}
    )
    print_pretty("Fetch by Email", response1)

    response2 = requests.get(f"{BASE_URL}/user", params={"cookie": "cookie999"})
    print_pretty("Fetch by New Cookie", response2)


# ---------- Test 4: Different Email and Cookie (should not merge) ----------


def test_different_email_cookie():
    payload = {
        "data": [
            {
                "cookie": "cookieABC",
                "email": "uniqueuser@example.com",
                "phone_number": "+1000000003",
                "location": {"state": "Texas", "country": "USA", "city": "Austin"},
                "demographics": {
                    "age": 32,
                    "gender": "Female",
                    "income": "$90,000-$110,000",
                    "education": "Master's",
                },
                "interests": ["cooking"],
            }
        ]
    }
    response = requests.post(f"{BASE_URL}/ingest", json=payload)
    print_pretty("New User Ingest", response)

    response1 = requests.get(
        f"{BASE_URL}/user", params={"email": "uniqueuser@example.com"}
    )
    print_pretty("Fetch by Email", response1)

    response2 = requests.get(f"{BASE_URL}/user", params={"cookie": "cookieABC"})
    print_pretty("Fetch by Cookie", response2)


if __name__ == "__main__":
    test_identity_initial_ingest()
    test_same_cookie_different_email()
    test_same_email_different_cookie()
    test_different_email_cookie()
