import requests
import json

BASE_URL = "http://localhost:8000/api"

# ---------- 1. Test Ingest Endpoint ----------


def test_ingest():
    ingest_payload = {
        "data": [
            {
                "cookie": "abc123cookie",
                "email": "user1@example.com",
                "phone_number": "+1234567890",
                "location": {
                    "state": "California",
                    "country": "USA",
                    "city": "Los Angeles",
                },
                "demographics": {
                    "age": 30,
                    "gender": "Male",
                    "income": "$80,000-$99,999",
                    "education": "Bachelor's Degree",
                },
                "interests": ["football", "basketball"],
            },
            {
                "cookie": "xyz456cookie",
                "email": "user2@example.com",
                "phone_number": "+1987654321",
                "location": {"state": "New York", "country": "USA", "city": "New York"},
                "demographics": {
                    "age": 25,
                    "gender": "Female",
                    "income": "$50,000-$69,999",
                    "education": "Master's Degree",
                },
                "interests": ["tennis", "fashion"],
            },
        ]
    }

    response = requests.post(f"{BASE_URL}/ingest", json=ingest_payload)
    print("Ingest Response:", response.status_code, response.json())


# ---------- 2. Test Get User by Email ----------


def test_get_user_by_email():
    params_email = {"email": "newemail@example.com"}
    response = requests.get(f"{BASE_URL}/user", params=params_email)
    print(
        "Get User by Email Response:",
        response.status_code,
        json.dumps(response.json(), indent=2),
    )


# ---------- 3. Test Get User by Cookie ----------


def test_get_user_by_cookie():
    params_cookie = {"cookie": "cookie999"}
    response = requests.get(f"{BASE_URL}/user", params=params_cookie)
    print(
        "Get User by Cookie Response:",
        response.status_code,
        json.dumps(response.json(), indent=2),
    )


# ---------- 4. Test Get Users by Cohort ----------


def test_get_users_by_cohort():
    params_cohort = {"cohort": "travel", "limit": 5, "offset": 0}
    response = requests.get(f"{BASE_URL}/cohort/users", params=params_cohort)
    print(
        "Get Users by Cohort Response:",
        response.status_code,
        json.dumps(response.json(), indent=2),
    )


if __name__ == "__main__":
    # test_ingest()
    test_get_user_by_email()
    test_get_user_by_cookie()
    test_get_users_by_cohort()
