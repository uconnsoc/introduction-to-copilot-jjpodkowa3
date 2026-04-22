"""
Test suite for FastAPI activity registration endpoints.
Uses the AAA (Arrange-Act-Assert) testing pattern for clarity and organization.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_all_activities_returns_success(self, client):
        """
        Arrange: No setup needed
        Act: Make GET request to /activities
        Assert: Response is 200 OK and returns a dictionary of activities
        """
        # Arrange - implicit from fixture

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # 9 predefined activities

    def test_activities_have_required_fields(self, client):
        """
        Arrange: No setup needed
        Act: Get activities and check structure
        Assert: Each activity has all required fields
        """
        # Arrange - implicit from fixture

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_chess_club_has_initial_participants(self, client):
        """
        Arrange: No setup needed
        Act: Get activities
        Assert: Chess Club has the expected initial participants
        """
        # Arrange - implicit from fixture

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        chess_club = data.get("Chess Club")
        assert chess_club is not None
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_with_valid_email_and_activity_returns_success(self, client):
        """
        Arrange: Basketball Team has no participants
        Act: Sign up a new student for Basketball Team
        Assert: Response is 200 OK and participant is added
        """
        # Arrange
        email = "alice@mergington.edu"
        activity = "Basketball Team"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert f"Signed up {email}" in data["message"]
        assert activity in data["message"]

    def test_participant_added_to_activity_list(self, client):
        """
        Arrange: Basketball Team is empty
        Act: Sign up a student
        Assert: Student appears in participants list on next GET request
        """
        # Arrange
        email = "alice@mergington.edu"
        activity = "Basketball Team"

        # Act
        client.post(f"/activities/{activity}/signup", params={"email": email})
        response = client.get("/activities")

        # Assert
        data = response.json()
        assert email in data[activity]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Activity 'Nonexistent Club' does not exist
        Act: Try to sign up for it
        Assert: Response is 404 Not Found
        """
        # Arrange
        email = "alice@mergington.edu"
        activity = "Nonexistent Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup_returns_400(self, client):
        """
        Arrange: michael@mergington.edu is already in Chess Club
        Act: Try to sign up for Chess Club again
        Assert: Response is 400 Bad Request with duplicate error
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_invalid_email_format_returns_400(self, client):
        """
        Arrange: Email without @ symbol
        Act: Try to sign up with invalid email
        Assert: Response is 400 Bad Request with email error
        """
        # Arrange
        email = "invalidemail"
        activity = "Basketball Team"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid email format" in data["detail"]

    def test_email_without_domain_returns_400(self, client):
        """
        Arrange: Email without domain extension
        Act: Try to sign up with incomplete email
        Assert: Response is 400 Bad Request
        """
        # Arrange
        email = "alice@mergington"
        activity = "Basketball Team"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_email_with_spaces_returns_400(self, client):
        """
        Arrange: Email with spaces
        Act: Try to sign up with invalid email
        Assert: Response is 400 Bad Request
        """
        # Arrange
        email = "alice @mergington.edu"
        activity = "Basketball Team"

        # Act
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid email format" in response.json()["detail"]

    def test_signup_when_activity_at_capacity_returns_400(self, client):
        """
        Arrange: Tennis Club has max_participants = 10 and 0 participants
        Act: Sign up 10 students, then try to sign up one more
        Assert: The 11th signup returns 400 with capacity error
        """
        # Arrange
        activity = "Tennis Club"
        emails = [f"student{i}@mergington.edu" for i in range(11)]

        # Act - Sign up first 10 students (should succeed)
        for i in range(10):
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": emails[i]}
            )
            assert response.status_code == 200

        # Act - Try to sign up the 11th student (should fail)
        response_overflow = client.post(
            f"/activities/{activity}/signup",
            params={"email": emails[10]}
        )

        # Assert
        assert response_overflow.status_code == 400
        data = response_overflow.json()
        assert "full capacity" in data["detail"]

    def test_signup_at_exactly_max_capacity_succeeds(self, client):
        """
        Arrange: Tennis Club has max_participants = 10
        Act: Sign up exactly 10 students
        Assert: All 10 signups succeed
        """
        # Arrange
        activity = "Tennis Club"
        emails = [f"student{i}@mergington.edu" for i in range(10)]

        # Act
        responses = []
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            responses.append(response)

        # Assert
        for response in responses:
            assert response.status_code == 200
        
        # Verify all are in the activity
        activities_response = client.get("/activities")
        activity_data = activities_response.json()[activity]
        assert len(activity_data["participants"]) == 10


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""

    def test_unregister_existing_participant_returns_success(self, client):
        """
        Arrange: michael@mergington.edu is in Chess Club
        Act: Unregister michael@mergington.edu from Chess Club
        Assert: Response is 200 OK and participant is removed
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert f"Unregistered {email}" in data["message"]

    def test_participant_removed_from_activity_list(self, client):
        """
        Arrange: michael@mergington.edu is in Chess Club
        Act: Unregister michael and then fetch activities
        Assert: michael is no longer in Chess Club participants
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act
        client.delete(f"/activities/{activity}/signup", params={"email": email})
        response = client.get("/activities")

        # Assert
        data = response.json()
        assert email not in data[activity]["participants"]
        assert len(data[activity]["participants"]) == 1  # daniel should remain

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Activity 'Nonexistent Club' does not exist
        Act: Try to unregister from it
        Assert: Response is 404 Not Found
        """
        # Arrange
        email = "alice@mergington.edu"
        activity = "Nonexistent Club"

        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_non_participant_returns_400(self, client):
        """
        Arrange: alice@mergington.edu is NOT in Basketball Team
        Act: Try to unregister alice from Basketball Team
        Assert: Response is 400 Bad Request with not registered error
        """
        # Arrange
        email = "alice@mergington.edu"
        activity = "Basketball Team"

        # Act
        response = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_then_signup_again_succeeds(self, client):
        """
        Arrange: michael@mergington.edu is in Chess Club
        Act: Unregister, then sign up again
        Assert: Both operations succeed
        """
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"

        # Act - Unregister
        response_delete = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response_delete.status_code == 200

        # Act - Sign up again
        response_signup = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response_signup.status_code == 200
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data[activity]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complex user workflows"""

    def test_signup_unregister_signup_workflow(self, client):
        """
        Arrange: Alice is not signed up for any activity
        Act: Sign up for activity -> unregister -> sign up again
        Assert: All operations succeed and state is correct
        """
        # Arrange
        email = "alice@mergington.edu"
        activity = "Basketball Team"

        # Act - Initial signup
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200

        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]

        # Act - Unregister
        response2 = client.delete(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 200

        # Verify unregister
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]

        # Act - Sign up again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200

        # Assert - Final state
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]

    def test_multiple_students_signup_and_unregister(self, client):
        """
        Arrange: No students in Basketball Team
        Act: Multiple students sign up, some unregister
        Assert: Participant list updates correctly
        """
        # Arrange
        activity = "Basketball Team"
        students = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]

        # Act - All sign up
        for student in students:
            client.post(f"/activities/{activity}/signup", params={"email": student})

        # Assert - All present
        activities = client.get("/activities").json()
        for student in students:
            assert student in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == 3

        # Act - Bob unregisters
        client.delete(f"/activities/{activity}/signup", params={"email": students[1]})

        # Assert - Bob gone, others remain
        activities = client.get("/activities").json()
        assert students[0] in activities[activity]["participants"]
        assert students[1] not in activities[activity]["participants"]
        assert students[2] in activities[activity]["participants"]
        assert len(activities[activity]["participants"]) == 2

    def test_availability_updates_correctly_after_signups(self, client):
        """
        Arrange: Tennis Club has max_participants = 10, currently 0 participants
        Act: Sign up 5 students, check availability via GET
        Assert: Availability shows correct remaining spots
        """
        # Arrange
        activity = "Tennis Club"
        max_capacity = 10
        emails = [f"student{i}@mergington.edu" for i in range(5)]

        # Act
        for email in emails:
            client.post(f"/activities/{activity}/signup", params={"email": email})
        
        response = client.get("/activities")
        activity_data = response.json()[activity]

        # Assert
        participants_count = len(activity_data["participants"])
        assert participants_count == 5
        # Frontend calculates availability as: max_participants - len(participants)
        expected_available = max_capacity - participants_count
        assert expected_available == 5
