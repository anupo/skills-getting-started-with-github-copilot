import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that get activities returns 200 status"""
        # Arrange
        expected_status = 200
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == expected_status
    
    def test_get_activities_returns_dict(self, client):
        """Test that get activities returns a dictionary"""
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert isinstance(data, dict)
    
    def test_get_activities_contains_expected_fields(self, client):
        """Test that activities contain expected fields"""
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert expected_fields.issubset(activity_data.keys())
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_returns_200(self, client, reset_activities):
        """Test successful signup returns 200"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        expected_status = 200
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "Signed up" in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds participant to activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        
        # Assert
        assert email in participants
    
    def test_signup_duplicate_email_returns_400(self, client, reset_activities):
        """Test that duplicate signup returns 400 error"""
        # Arrange
        email = "michael@mergington.edu"  # Already registered
        activity = "Chess Club"
        expected_status = 400
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signup for non-existent activity returns 404"""
        # Arrange
        email = "test@mergington.edu"
        activity = "NonExistent Club"
        expected_status = 404
        
        # Act
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_increments_participant_count(self, client, reset_activities):
        """Test that signup increments participant count"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity]["participants"])
        
        # Act
        client.post(f"/activities/{activity}/signup?email={email}")
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity]["participants"])
        
        # Assert
        assert count_after == count_before + 1


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_participant_returns_200(self, client, reset_activities):
        """Test successful unregister returns 200"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        expected_status = 200
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant_from_activity(self, client, reset_activities):
        """Test that unregister actually removes participant"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Act
        client.delete(f"/activities/{activity}/unregister?email={email}")
        response = client.get("/activities")
        participants = response.json()[activity]["participants"]
        
        # Assert
        assert email not in participants
    
    def test_unregister_nonexistent_participant_returns_404(self, client, reset_activities):
        """Test that unregistering non-existent participant returns 404"""
        # Arrange
        email = "nonexistent@mergington.edu"
        activity = "Chess Club"
        expected_status = 404
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "not registered" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregister from non-existent activity returns 404"""
        # Arrange
        email = "test@mergington.edu"
        activity = "NonExistent Club"
        expected_status = 404
        
        # Act
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Assert
        assert response.status_code == expected_status
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_decrements_participant_count(self, client, reset_activities):
        """Test that unregister decrements participant count"""
        # Arrange
        email = "michael@mergington.edu"
        activity = "Chess Club"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity]["participants"])
        
        # Act
        client.delete(f"/activities/{activity}/unregister?email={email}")
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity]["participants"])
        
        # Assert
        assert count_after == count_before - 1


class TestIntegration:
    """Integration tests for complete signup/unregister workflows"""
    
    def test_signup_then_unregister_workflow(self, client, reset_activities):
        """Test complete signup and unregister workflow"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act - Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        verify_signup = client.get("/activities")
        
        # Assert - Signup successful
        assert signup_response.status_code == 200
        assert email in verify_signup.json()[activity]["participants"]
        
        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        verify_unregister = client.get("/activities")
        
        # Assert - Unregister successful
        assert unregister_response.status_code == 200
        assert email not in verify_unregister.json()[activity]["participants"]
    
    def test_multiple_students_signup_and_selective_unregister(self, client, reset_activities):
        """Test multiple students signing up then unregistering one"""
        # Arrange
        activity = "Chess Club"
        students = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu"
        ]
        
        # Act - All students signup
        for email in students:
            client.post(f"/activities/{activity}/signup?email={email}")
        verify_all_signups = client.get("/activities")
        
        # Assert - All signed up
        for email in students:
            assert email in verify_all_signups.json()[activity]["participants"]
        
        # Act - Unregister first student
        client.delete(f"/activities/{activity}/unregister?email={students[0]}")
        verify_after_unregister = client.get("/activities")
        participants_after = verify_after_unregister.json()[activity]["participants"]
        
        # Assert - First unregistered, others still registered
        assert students[0] not in participants_after
        assert students[1] in participants_after
        assert students[2] in participants_after
