#!/usr/bin/env python3
"""
Simple API test script to verify SQLAlchemy migration worked correctly.
Tests all endpoints without pytest dependency.
"""

import asyncio
import httpx
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.access_token = None
        self.headers = {}
        self.user_id = None
        self.note_id = None
        
    async def run_all_tests(self):
        """Run all API tests sequentially."""
        print("🧪 Starting API Tests for SQLAlchemy Migration")
        print("=" * 60)
        
        async with httpx.AsyncClient() as client:
            try:
                await self.test_00_cleanup_test_data(client)
                await self.test_01_server_health(client)
                await self.test_02_user_registration(client)
                await self.test_03_user_login(client)
                await self.test_04_find_user_id(client)
                await self.test_05_change_password(client)
                await self.test_06_create_patient(client)
                await self.test_07_assign_patient_to_doctor(client)
                await self.test_08_get_all_patients(client)
                await self.test_09_get_specific_patient(client)
                await self.test_10_create_note(client)
                await self.test_11_get_all_notes(client)
                await self.test_12_get_specific_note(client)
                await self.test_13_update_note(client)
                await self.test_14_unauthorized_access(client)
                await self.test_15_error_cases(client)
                
                print("\n✅ All tests passed! SQLAlchemy migration successful!")
                
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                raise

    async def test_00_cleanup_test_data(self, client):
        """Clean up any existing test data before running tests."""
        print("🧹 Cleaning up existing test data...")
        
        # We'll need to connect directly to the database to clean up
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from app.core.db import AsyncSessionLocal, User, Patient, Note, doctor_patient_association
        from sqlalchemy import select, delete
        
        async with AsyncSessionLocal() as db:
            try:
                # Delete relationship data first (to avoid foreign key constraints)
                await db.execute(delete(doctor_patient_association).where(
                    doctor_patient_association.c.doctor_id.like("testdoctor%")
                ))
                await db.execute(delete(doctor_patient_association).where(
                    doctor_patient_association.c.patient_mrn == "P12345"
                ))
                
                # Delete test notes (references patient and doctor)
                await db.execute(delete(Note).where(Note.patient_mrn == "P12345"))
                
                # Delete test patient data  
                await db.execute(delete(Patient).where(Patient.patient_mrn == "P12345"))
                
                # Delete test user data (last, since others reference it)
                await db.execute(delete(User).where(User.user_id.like("testdoctor%")))
                await db.execute(delete(User).where(User.email.like("test%@example.com")))
                
                await db.commit()
                print("✅ Test data cleanup completed")
                
            except Exception as e:
                print(f"⚠️  Cleanup warning (this is normal on first run): {e}")
                await db.rollback()

    async def test_01_server_health(self, client):
        """Test server health endpoint."""
        print("🔍 Testing server health...")
        response = await client.get(f"{BASE_URL}/server_on")
        assert response.status_code == 200
        assert response.json() == {"server_on": True}
        print("✅ Server health check passed")

    async def test_02_user_registration(self, client):
        """Test user registration."""
        print("🔍 Testing user registration...")
        user_data = {
            "email": "test@example.com",
            "phone_num": "01012345678",
            "name": {
                "first_name": "John",
                "last_name": "Doe"
            },
            "user_id": "testdoctor",
            "password": "testpassword123",
            "position": "doctor",
            "licence_num": "DOC123456"
        }
        
        response = await client.post(f"{BASE_URL}/auth/register", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "registered"
        assert "_id" in data
        self.user_id = data["_id"]
        print("✅ User registration passed")

    async def test_03_user_login(self, client):
        """Test user login."""
        print("🔍 Testing user login...")
        login_data = {
            "user_id": "testdoctor",
            "password": "testpassword123"
        }
        
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "Bearer"
        
        self.access_token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        print("✅ User login passed")

    async def test_04_find_user_id(self, client):
        """Test find user ID."""
        print("🔍 Testing find user ID...")
        find_data = {
            "phone_num": "01012345678",
            "name": {
                "first_name": "John",
                "last_name": "Doe"
            }
        }
        
        response = await client.post(f"{BASE_URL}/auth/find_id", json=find_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["user_id"] == "testdoctor"
        print("✅ Find user ID passed")

    async def test_05_change_password(self, client):
        """Test change password."""
        print("🔍 Testing change password...")
        change_pw_data = {
            "user_id": "testdoctor",
            "name": {
                "first_name": "John",
                "last_name": "Doe"
            },
            "original_pw": "testpassword123",
            "new_pw": "newpassword123"
        }
        
        response = await client.post(f"{BASE_URL}/auth/change_pw", json=change_pw_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Test login with new password
        login_data = {
            "user_id": "testdoctor",
            "password": "newpassword123"
        }
        response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
        assert response.status_code == 200
        
        # Update token
        self.access_token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        print("✅ Change password passed")

    async def test_06_create_patient(self, client):
        """Test patient creation."""
        print("🔍 Testing patient creation...")
        patient_data = {
            "phone_num": "01087654321",
            "patient_mrn": "P12345",
            "name": {
                "first_name": "Jane",
                "last_name": "Smith"
            },
            "age": 42,
            "body_part": ["brain"],
            "ai_ready": True
        }
        
        response = await client.post(f"{BASE_URL}/patients/create", json=patient_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✅ Patient creation passed")

    async def test_07_assign_patient_to_doctor(self, client):
        """Test patient assignment."""
        print("🔍 Testing patient assignment...")
        response = await client.post(
            f"{BASE_URL}/patients/assign/P12345",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("✅ Patient assignment passed")

    async def test_08_get_all_patients(self, client):
        """Test get all patients."""
        print("🔍 Testing get all patients...")
        response = await client.get(f"{BASE_URL}/patients/", headers=self.headers)
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "patients" in data
        assert len(data["patients"]) > 0
        print("✅ Get all patients passed")

    async def test_09_get_specific_patient(self, client):
        """Test get specific patient."""
        print("🔍 Testing get specific patient...")
        response = await client.get(
            f"{BASE_URL}/patients/P12345",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "patient" in data
        assert data["patient"]["patient_mrn"] == "P12345"
        print("✅ Get specific patient passed")

    async def test_10_create_note(self, client):
        """Test note creation."""
        print("🔍 Testing note creation...")
        note_data = {
            "title": "Test Medical Note",
            "content": "Patient shows improvement after treatment",
            "note_type": "consult"
        }
        
        response = await client.post(
            f"{BASE_URL}/notes/create/P12345",
            json=note_data,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "note" in data
        self.note_id = data["note"]["id"]
        print("✅ Note creation passed")

    async def test_11_get_all_notes(self, client):
        """Test get all notes."""
        print("🔍 Testing get all notes...")
        response = await client.get(
            f"{BASE_URL}/notes/all/P12345",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "notes" in data
        assert len(data["notes"]) > 0
        print("✅ Get all notes passed")

    async def test_12_get_specific_note(self, client):
        """Test get specific note."""
        print("🔍 Testing get specific note...")
        response = await client.get(
            f"{BASE_URL}/notes/{self.note_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "note" in data
        assert data["note"]["id"] == self.note_id
        print("✅ Get specific note passed")

    async def test_13_update_note(self, client):
        """Test note update."""
        print("🔍 Testing note update...")
        update_data = {
            "patient_mrn": "P12345",
            "title": "Updated Medical Note",
            "content": "Updated content with new findings",
            "note_type": "radiology"
        }
        
        response = await client.post(
            f"{BASE_URL}/notes/update/{self.note_id}",
            json=update_data,
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["note"]["title"] == "Updated Medical Note"
        assert data["note"]["note_type"] == "radiology"
        print("✅ Note update passed")

    async def test_14_unauthorized_access(self, client):
        """Test unauthorized access."""
        print("🔍 Testing unauthorized access...")
        
        # Test without token
        response = await client.get(f"{BASE_URL}/patients/")
        assert response.status_code == 401
        
        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get(f"{BASE_URL}/patients/", headers=invalid_headers)
        assert response.status_code == 401
        print("✅ Unauthorized access tests passed")

    async def test_15_error_cases(self, client):
        """Test error cases."""
        print("🔍 Testing error cases...")
        
        # Test nonexistent patient
        response = await client.get(
            f"{BASE_URL}/patients/NONEXISTENT",
            headers=self.headers
        )
        assert response.status_code == 404
        
        # Test nonexistent note
        response = await client.get(
            f"{BASE_URL}/notes/nonexistent_note_id",
            headers=self.headers
        )
        assert response.status_code == 404
        
        # Test invalid login
        invalid_login = {
            "user_id": "nonexistent",
            "password": "wrongpassword"
        }
        response = await client.post(f"{BASE_URL}/auth/login", json=invalid_login)
        assert response.status_code == 401
        
        print("✅ Error cases passed")

async def main():
    """Main test runner."""
    print("🚀 API Test Suite for SQLAlchemy Migration")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    try:
        # Check if server is running
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/server_on", timeout=5.0)
            if response.status_code != 200:
                raise Exception("Server not responding")
        
        # Run tests
        tester = APITester()
        await tester.run_all_tests()
        
    except httpx.ConnectError:
        print("❌ Error: Server not running. Please start the server with: python server.py")
        return False
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)
    
    print("\n🎉 All tests completed successfully!")
    print("✅ SQLAlchemy migration verification complete!")