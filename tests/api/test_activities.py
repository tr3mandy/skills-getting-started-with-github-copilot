from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activity_state():
    original_participants = {
        activity_name: list(details["participants"])
        for activity_name, details in activities.items()
    }

    yield

    for activity_name, details in activities.items():
        details["participants"] = original_participants[activity_name][:]


def test_get_activities_returns_catalog():
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_and_unregister_activity_flow():
    email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    signup_response = client.post(
        f"/activities/{quote(activity_name)}/signup?email={quote(email)}"
    )
    assert signup_response.status_code == 200
    assert signup_response.json()["message"] == f"Signed up {email} for {activity_name}"

    updated_activity = client.get("/activities").json()[activity_name]
    assert email in updated_activity["participants"]

    unregister_response = client.delete(
        f"/activities/{quote(activity_name)}/signup?email={quote(email)}"
    )
    assert unregister_response.status_code == 200
    assert unregister_response.json()["message"] == f"Unregistered {email} from {activity_name}"

    final_activity = client.get("/activities").json()[activity_name]
    assert email not in final_activity["participants"]


def test_signup_missing_activity_returns_404():
    response = client.post("/activities/Unknown Club/signup?email=test@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate_student_returns_400():
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    response = client.post(
        f"/activities/{quote(activity_name)}/signup?email={quote(email)}"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_unregister_nonexistent_participant_returns_404():
    email = "missing@mergington.edu"
    activity_name = "Chess Club"

    response = client.delete(
        f"/activities/{quote(activity_name)}/signup?email={quote(email)}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
