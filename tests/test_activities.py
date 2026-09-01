from urllib.parse import quote

from fastapi.testclient import TestClient

from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self):
        """Test fetching all activities."""
        response = client.get("/activities")

        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has the required structure."""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_adds_participant_to_activity(self):
        """Test that a new participant can sign up for an activity."""
        activity_name = "Tennis Club"
        email = "test_student@mergington.edu"

        response = client.post(
            f"/activities/{quote(activity_name)}/signup?email={quote(email)}"
        )

        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"

        # Verify participant was added
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

    def test_signup_for_nonexistent_activity_returns_404(self):
        """Test that signup fails for an activity that doesn't exist."""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_participant_returns_400(self):
        """Test that a student cannot sign up twice for the same activity."""
        activity_name = "Art Studio"
        email = "sarah@mergington.edu"  # Already signed up

        response = client.post(
            f"/activities/{quote(activity_name)}/signup?email={quote(email)}"
        )

        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_with_empty_email_fails(self):
        """Test that signup with missing email is rejected."""
        response = client.post("/activities/Chess%20Club/signup")

        # FastAPI validates query params, should return 422 Unprocessable Entity
        assert response.status_code == 422


class TestParticipantRemovalEndpoint:
    """Test the DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_unregister_participant_removes_email_from_activity(self):
        """Test that a participant can be removed from an activity."""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        response = client.delete(
            f"/activities/{quote(activity_name)}/participants/{quote(email)}"
        )

        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"

        activity = client.get("/activities").json()[activity_name]
        assert email not in activity["participants"]

    def test_unregister_unknown_participant_returns_404(self):
        """Test that unregistering a non-existent participant fails."""
        response = client.delete(
            "/activities/Chess%20Club/participants/nonexistent@mergington.edu"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found in this activity"

    def test_unregister_from_nonexistent_activity_returns_404(self):
        """Test that unregistering from a non-existent activity fails."""
        response = client.delete(
            "/activities/Fake%20Club/participants/student@mergington.edu"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"


class TestRootEndpoint:
    """Test the GET / endpoint."""

    def test_root_redirects_to_static_html(self):
        """Test that the root endpoint redirects to the static index page."""
        response = client.get("/", follow_redirects=False)

        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
