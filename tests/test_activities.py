"""
Tests for the Mergington High School Activities API using the AAA pattern.
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: client is prepared with known activities
        Act: fetch all activities
        Assert: status 200 and all expected activities are returned
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_returns_complete_activity_structure(self, client):
        """
        Arrange: client is prepared
        Act: fetch activities
        Assert: each activity has required fields (description, schedule, max_participants, participants)
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_includes_existing_participants(self, client):
        """
        Arrange: Chess Club has known participants
        Act: fetch activities
        Assert: participants list includes the expected emails
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in participants
        assert "daniel@mergington.edu" in participants


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful_adds_participant(self, client):
        """
        Arrange: choose a new email not in Chess Club
        Act: send signup request
        Assert: status 200, success message returned, participant added
        """
        # Arrange
        new_email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_email in data["message"]
        
        # Verify participant was actually added
        verify_response = client.get("/activities")
        activities_data = verify_response.json()
        assert new_email in activities_data["Chess Club"]["participants"]

    def test_signup_duplicate_email_returns_400(self, client):
        """
        Arrange: michael@mergington.edu is already in Chess Club
        Act: attempt signup with same email
        Assert: status 400 and appropriate error message
        """
        # Arrange
        existing_email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: use a fake activity name
        Act: send signup request
        Assert: status 404 and activity not found message
        """
        # Arrange
        fake_activity = "Fake Club"
        new_email = "test@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_with_special_characters_in_activity_name(self, client):
        """
        Arrange: activity name with spaces (URL-encoded)
        Act: send signup request
        Assert: status 200 (activity exists and spaces are handled)
        """
        # Arrange
        new_email = "test123@mergington.edu"
        
        # Act
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response.status_code == 200
        verify_response = client.get("/activities")
        activities_data = verify_response.json()
        assert new_email in activities_data["Chess Club"]["participants"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""

    def test_remove_participant_successful(self, client):
        """
        Arrange: michael@mergington.edu is in Chess Club
        Act: send delete request
        Assert: status 200, participant removed from list
        """
        # Arrange
        email_to_remove = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/Chess%20Club/participants/{email_to_remove}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify participant was actually removed
        verify_response = client.get("/activities")
        activities_data = verify_response.json()
        assert email_to_remove not in activities_data["Chess Club"]["participants"]

    def test_remove_nonexistent_participant_returns_400(self, client):
        """
        Arrange: fake@mergington.edu is not in Chess Club
        Act: send delete request
        Assert: status 400 and error message
        """
        # Arrange
        nonexistent_email = "fake@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/Chess%20Club/participants/{nonexistent_email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_remove_participant_from_nonexistent_activity_returns_404(self, client):
        """
        Arrange: use a fake activity name
        Act: send delete request
        Assert: status 404
        """
        # Arrange
        fake_activity = "Fake Club"
        email = "test@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{fake_activity}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""

    def test_full_signup_and_removal_cycle(self, client):
        """
        Arrange: fresh Chess Club state
        Act: signup new student, verify added, remove, verify removed
        Assert: each step succeeds with correct state
        """
        # Arrange
        new_email = "integration@mergington.edu"
        
        # Act - Signup
        signup_response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_email}
        )
        assert signup_response.status_code == 200
        
        # Assert - Verify added
        verify1 = client.get("/activities")
        assert new_email in verify1.json()["Chess Club"]["participants"]
        
        # Act - Remove
        remove_response = client.delete(
            f"/activities/Chess%20Club/participants/{new_email}"
        )
        assert remove_response.status_code == 200
        
        # Assert - Verify removed
        verify2 = client.get("/activities")
        assert new_email not in verify2.json()["Chess Club"]["participants"]

    def test_multiple_signups_to_different_activities(self, client):
        """
        Arrange: multiple activities available
        Act: signup same student to multiple activities
        Assert: participant appears in both activities
        """
        # Arrange
        new_email = "multi@mergington.edu"
        
        # Act
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_email}
        )
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": new_email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        verify = client.get("/activities")
        data = verify.json()
        assert new_email in data["Chess Club"]["participants"]
        assert new_email in data["Programming Class"]["participants"]
