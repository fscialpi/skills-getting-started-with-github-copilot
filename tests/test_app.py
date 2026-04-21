from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    """Keep tests isolated by restoring in-memory activities each test."""
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_activities))


def test_get_activities_returns_all_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert {"description", "schedule", "max_participants", "participants"}.issubset(
        data["Chess Club"].keys()
    )


def test_signup_for_activity_success():
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    body = response.json()
    assert "Signed up" in body["message"]
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_not_found():
    response = client.post("/activities/Unknown%20Activity/signup", params={"email": "ghost@mergington.edu"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_activity_duplicate_participant():
    activity_name = "Programming Class"
    existing_email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_unregister_participant_success():
    activity_name = "Drama Club"
    existing_email = activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": existing_email},
    )

    assert response.status_code == 200
    body = response.json()
    assert "Unregistered" in body["message"]
    assert existing_email not in activities[activity_name]["participants"]


def test_unregister_participant_activity_not_found():
    response = client.delete(
        "/activities/Unknown%20Activity/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_not_found_in_activity():
    response = client.delete(
        "/activities/Chess%20Club/participants",
        params={"email": "notenrolled@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"
