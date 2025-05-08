from locust import HttpUser, task, between
import random
import uuid
from datetime import date, timedelta
import json

FIXED_DATES = [
    # (date.today() - timedelta(days=30)).isoformat(), # Approx 1 month ago
    (date.today() - timedelta(days=1)).isoformat(),  # Yesterday
    date.today().isoformat(),  # Today
]

FIXED_VALUES = [1, 3, 5, 7, 10]


class MoodDiaryUser(HttpUser):
    host = "https://mood-diary.duckdns.org/api"
    wait_time = between(1, 5)

    def on_start(self):
        """
        Called when the user starts golfing.
        Registers and logs in a user for each Locust user instance.
        """
        self.username = f"user_{uuid.uuid4().hex[:8]}"
        self.password = "Test@1234"
        self.register_user()
        self.login_user()
        self.created_date_str = None

    def register_user(self):
        """Registers a new user"""
        payload = {
            "username": self.username,
            "password": self.password,
            "name": "Test User",
        }
        response = self.client.post("/auth/register", json=payload)
        response.raise_for_status()

    def login_user(self):
        """Logs in the user and stores the access token"""
        payload = {"username": self.username, "password": self.password}
        response = self.client.post("/auth/login", json=payload)
        response.raise_for_status()

        self.token = response.cookies.get("access_token")
        if not self.token:
            try:
                login_response = response.json()
                if "access_token" in login_response:
                    self.token = login_response["access_token"]
                    self.headers = {"Authorization": f"Bearer {self.token}"}
                    return
                else:
                    raise Exception(
                        "Access token not found in cookies or response body."
                    )
            except json.JSONDecodeError:
                raise Exception("Login response is not JSON, token not found.")
            except Exception as e:
                raise Exception(
                    f"Login successful, but failed to get access token: {e}"
                )
        else:
            pass

    # --- Mood Stamp Tasks ---

    @task(10)
    def get_many_moodstamps(self):
        """Fetches multiple mood stamps"""
        headers = getattr(self, "headers", {})

        params = {}
        if random.random() < 0.5:  # 50% chance to add value filter
            params["value"] = random.choice(FIXED_VALUES)

        response = self.client.get("/mood/", params=params, headers=headers)
        response.raise_for_status()

    @task(20)
    def create_moodstamp(self):
        """Creates a new mood stamp"""
        selected_date_str = random.choice(FIXED_DATES)
        selected_value = random.choice(FIXED_VALUES)

        payload = {
            "date": selected_date_str,
            "value": selected_value,
            "note": f"Feeling {random.choice(['great', 'okay', 'bad', 'tired', 'happy', 'sad', 'neutral'])}!",
        }
        headers = {"Content-Type": "application/json"}
        headers.update(getattr(self, "headers", {}))

        response = self.client.post("/mood/", json=payload, headers=headers)

        try:
            response.raise_for_status()
            self.created_date_str = selected_date_str
        except Exception as e:
            pass

    @task(2)
    def get_single_moodstamp(self):
        """Fetches a specific mood stamp by date"""
        if self.created_date_str:
            date_str = self.created_date_str
            headers = getattr(self, "headers", {})

            response = self.client.get(f"/mood/{date_str}", headers=headers)
            response.raise_for_status()

    @task(2)  # Lower weight for updating
    def update_moodstamp(self):
        """Updates an existing mood stamp"""
        if self.created_date_str:
            date_str = self.created_date_str
            selected_value = random.choice(FIXED_VALUES)
            payload = {
                "value": selected_value,
                "note": f"Updated note: Feeling {random.choice(['better', 'worse', 'the same', 'different'])}!",
            }
            headers = {"Content-Type": "application/json"}
            headers.update(getattr(self, "headers", {}))

            response = self.client.put(
                f"/mood/{date_str}", json=payload, headers=headers
            )
            response.raise_for_status()

    @task(1)  # Even lower weight for deleting (less frequent)
    def delete_moodstamp(self):
        """Deletes an existing mood stamp"""
        if self.created_date_str:
            date_str = self.created_date_str
            headers = getattr(self, "headers", {})

            response = self.client.delete(f"/mood/{date_str}", headers=headers)
            response.raise_for_status()
            self.created_date_str = None
