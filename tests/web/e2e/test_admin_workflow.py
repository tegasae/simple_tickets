import pytest
from fastapi.testclient import TestClient


class TestAdminWorkflowsE2E:
    """E2E tests for admin workflows"""

    def test_create_and_retrieve_admin(self, client, sample_admin_data):
        """E2E: Create admin and then retrieve it"""
        # Create admin
        create_response = client.post("/admins/", json=sample_admin_data)
        assert create_response.status_code == 201
        created_data = create_response.json()

        # Verify response structure
        assert "admin_id" in created_data
        assert created_data["name"] == sample_admin_data["name"]
        assert created_data["email"] == sample_admin_data["email"]
        assert created_data["enabled"] == sample_admin_data["enabled"]

        # Retrieve by ID
        admin_id = created_data["admin_id"]
        get_response = client.get(f"/admins/{admin_id}")
        assert get_response.status_code == 200

        # Verify data consistency
        retrieved_data = get_response.json()
        assert created_data["name"] == retrieved_data["name"]
        assert created_data["email"] == retrieved_data["email"]

    def test_full_admin_lifecycle(self, client, sample_admin_data):
        """E2E: Complete admin lifecycle"""
        # Create
        response = client.post("/admins/", json=sample_admin_data)
        assert response.status_code == 201
        admin_id = response.json()["admin_id"]

        # Update
        update_data = {"email": "updated@example.com"}
        update_response = client.put(f"/admins/{admin_id}", json=update_data)
        assert update_response.status_code == 200

        # Verify update
        get_response_after_update = client.get(f"/admins/{admin_id}")
        assert get_response_after_update.status_code == 200
        assert get_response_after_update.json()["email"] == "updated@example.com"

        # Delete
        delete_response = client.delete(f"/admins/{admin_id}")
        assert delete_response.status_code == 204

        # Verify deletion
        get_response_after_delete = client.get(f"/admins/{admin_id}")
        # This might return 404 or your custom error handling
        assert get_response_after_delete.status_code in [404, 500]

    def test_get_all_admins(self, client, sample_admin_data):
        """E2E: Test retrieving all admins"""
        # First, create an admin
        create_response = client.post("/admins/", json=sample_admin_data)
        assert create_response.status_code == 201

        # Then get all admins
        get_all_response = client.get("/admins/")
        assert get_all_response.status_code == 200

        admins_list = get_all_response.json()
        assert isinstance(admins_list, list)
        assert len(admins_list) >= 1

        # Verify our created admin is in the list
        admin_names = [admin["name"] for admin in admins_list]
        assert sample_admin_data["name"] in admin_names

    def test_check_admin_exists(self, client, sample_admin_data):
        """E2E: Test admin existence check"""
        # Check for non-existent admin
        check_response = client.get("/admins/check/nonexistent/exists")
        assert check_response.status_code == 200
        assert check_response.json() == {"exists": False}

        # Create an admin
        create_response = client.post("/admins/", json=sample_admin_data)
        assert create_response.status_code == 201

        # Check that it now exists
        check_response = client.get(f"/admins/check/{sample_admin_data['name']}/exists")
        assert check_response.status_code == 200
        assert check_response.json() == {"exists": True}