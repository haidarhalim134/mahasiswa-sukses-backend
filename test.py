import json
import requests

BASE_URL = "http://localhost:8000/api/v1"

EMAIL = "idaydiar6@gmail.com"
PASSWORD = "StrongPassword123"


def register():
    print("\nREGISTER")

    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }

    r = requests.post(f"{BASE_URL}/auth/register", json=payload)

    print(r.status_code)
    print(r.json())


def login():
    print("\nLOGIN")

    payload = {
        "email": EMAIL,
        "password": PASSWORD
    }

    r = requests.post(f"{BASE_URL}/auth/login", json=payload)

    print(r.status_code)
    data = r.json()
    print(data)

    return data["access_token"]


def test_user_route(token):
    print("\nTEST USER ROUTE")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(
        f"{BASE_URL}/me",
        headers=headers
    )

    print(r.status_code)
    print(r.json())


def test_admin_route(token):
    print("\nTEST ADMIN ROUTE")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(
        f"{BASE_URL}/admin/dashboard",
        headers=headers
    )

    print(r.status_code)
    print(r.json())


def test_reset_password():
    print("\nRESET PASSWORD")

    payload = {
        "email": EMAIL
    }

    r = requests.post(
        f"{BASE_URL}/auth/reset-password",
        json=payload
    )

    print(r.status_code)
    print(r.json())


def main():

    # register()

    token = login()

    test_user_route(token)

    test_admin_route(token)

    # test_reset_password()


if __name__ == "__main__":
    main()