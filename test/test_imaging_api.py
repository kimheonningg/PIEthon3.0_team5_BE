#!/usr/bin/env python3
"""
Comprehensive imaging API test with dynamic user/patient management.
Tests imaging endpoints with flexible user/patient creation and cleanup.
"""

import asyncio
import httpx
import sys
import os
from typing import Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

class ImagingAPITester:
    def __init__(self, use_existing_user: bool = False, existing_user_id: Optional[str] = None, existing_patient_mrn: Optional[str] = None):
        self.use_existing_user = use_existing_user
        self.existing_user_id = existing_user_id
        self.existing_patient_mrn = existing_patient_mrn
        
        # Test identifiers
        self.test_user_id = existing_user_id or "imaging_test_doctor"
        self.test_patient_mrn = existing_patient_mrn or "IMG_P12345"
        
        # API state
        self.access_token = None
        self.headers = {}
        
        # Created resources for cleanup
        self.created_subject_id = None
        self.created_series_ids = []
        self.created_disease_ids = []
        self.created_user = False
        self.created_patient = False
    
    async def run_all_tests(self):
        """Run all imaging API tests."""
        print("🏥 Starting Imaging API Tests")
        print("=" * 60)
        
        async with httpx.AsyncClient() as client:
            try:
                # Setup phase
                await self.setup_test_environment(client)
                await self.authenticate_user(client)
                
                # Core imaging tests
                await self.test_create_complete_imaging_study(client)
                await self.test_get_patient_imaging_studies(client)
                await self.test_get_imaging_subject_detail(client)
                await self.test_get_patient_imaging_summary(client)
                await self.test_update_disease_annotation(client)
                await self.test_individual_endpoints(client)
                
                
                # Test error cases
                await self.test_error_cases(client)
                
                print("\n✅ All imaging tests passed!")
                
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                raise
            finally:
                # Cleanup phase
                await self.cleanup_test_environment(client)

    async def setup_test_environment(self, client):
        """Setup test user and patient if needed."""
        print("🔧 Setting up test environment...")
        
        if not self.use_existing_user:
            await self.create_test_user(client)
            await self.create_test_patient(client)
        else:
            print(f"   Using existing user: {self.test_user_id}")
            print(f"   Using existing patient: {self.test_patient_mrn}")

    async def create_test_user(self, client):
        """Create a test user."""
        print("   Creating test user...")
        user_data = {
            "email": "imaging_test@example.com",
            "phone_num": "01099887766",
            "name": {
                "first_name": "Imaging",
                "last_name": "Tester"
            },
            "user_id": self.test_user_id,
            "password": "imaging_test_password123",
            "position": "doctor",
            "licence_num": "IMG_DOC123456"
        }
        
        response = await client.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            self.created_user = True
            print("   ✅ Test user created")
        else:
            print(f"   ⚠️  User creation failed (may already exist): {response.status_code}")

    async def create_test_patient(self, client):
        """Create a test patient."""
        print("   Creating test patient...")
        patient_data = {
            "phone_num": "01099887755",
            "patient_mrn": self.test_patient_mrn,
            "name": {
                "first_name": "Brain",
                "last_name": "Scan Patient"
            },
            "age": 35,
            "birthdate": "1988-01-15T00:00:00",
            "body_part": ["brain"],
            "ai_ready": True,
            "gender": "female"
        }
        
        response = await client.post(f"{BASE_URL}/patients/create", json=patient_data)
        if response.status_code == 200:
            self.created_patient = True
            print("   ✅ Test patient created")
        else:
            print(f"   ⚠️  Patient creation failed (may already exist): {response.status_code}")

    async def authenticate_user(self, client):
        """Authenticate the test user."""
        print("🔐 Authenticating user...")
        
        # Try different passwords for existing vs new users
        passwords_to_try = [
            "imaging_test_password123",  # New test user password
            "newpassword123",           # Updated password from main test
            "testpassword123"           # Original test password
        ]
        
        authenticated = False
        for password in passwords_to_try:
            login_data = {
                "user_id": self.test_user_id,
                "password": password
            }
            
            response = await client.post(f"{BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.access_token}"}
                authenticated = True
                break
        
        assert authenticated, f"Failed to authenticate with user {self.test_user_id} - tried multiple passwords"
        
        # Assign patient to doctor if we created both
        if self.created_user and self.created_patient:
            assign_response = await client.post(
                f"{BASE_URL}/patients/assign/{self.test_patient_mrn}",
                headers=self.headers
            )
            if assign_response.status_code != 200:
                print(f"   ⚠️  Patient assignment failed: {assign_response.status_code}")
        
        # Also try to assign if using existing user but created patient
        if not self.created_user and self.created_patient:
            assign_response = await client.post(
                f"{BASE_URL}/patients/assign/{self.test_patient_mrn}",
                headers=self.headers
            )
            if assign_response.status_code != 200:
                print(f"   ⚠️  Patient assignment failed: {assign_response.status_code}")
        
        # Always try to assign - this handles the case where user exists but patient was just created
        if self.created_patient:
            assign_response = await client.post(
                f"{BASE_URL}/patients/assign/{self.test_patient_mrn}",
                headers=self.headers
            )
            if assign_response.status_code == 200:
                print(f"   ✅ Patient {self.test_patient_mrn} assigned to doctor {self.test_user_id}")
            else:
                print(f"   ⚠️  Patient assignment failed: {assign_response.status_code} - {assign_response.text}")
        
        print("   ✅ User authenticated and patient assigned")

    async def test_create_complete_imaging_study(self, client):
        """Test creating a complete imaging study."""
        print("🔍 Testing complete imaging study creation...")
        
        study_data = {
            "subject_data": {
                "subject_name": "BraTS20_Validation_004",
                "patient_mrn": self.test_patient_mrn,
                "modality": "mri",
                "body_part": "brain",
                "study_description": "Brain tumor MRI - BraTS20 Validation"
            },
            "series_data": [
                {
                    "sequence_type": "t1",
                    "file_uri": "https://cdn.kiminjae.me/piethon-viewer/BraTS20_Validation_004/BraTS20_Validation_004_t1.nii",
                    "slices_dir": "https://cdn.kiminjae.me/BraTS20_Validation_004/slices/t1/",
                    "slice_idx": 98,
                    "image_resolution": "240x240"
                },
                {
                    "sequence_type": "t2",
                    "file_uri": "https://cdn.kiminjae.me/piethon-viewer/BraTS20_Validation_004/BraTS20_Validation_004_t2.nii",
                    "slices_dir": "https://cdn.kiminjae.me/BraTS20_Validation_004/slices/t2/",
                    "slice_idx": 98,
                    "image_resolution": "240x240"
                }
            ],
            "disease_data": [
                {
                    "series_index": 0,
                    "bounding_box": {
                        "x1": 67, "y1": 69, "x2": 126, "y2": 134
                    },
                    "confidence_score": 0.68381,
                    "class_name": "brain_tumour"
                },
                {
                    "series_index": 1,
                    "bounding_box": {
                        "x1": 64, "y1": 68, "x2": 148, "y2": 135
                    },
                    "confidence_score": 0.66649,
                    "class_name": "brain_tumour"
                }
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/imaging/studies",
            json=study_data,
            headers=self.headers
        )
        
        if response.status_code != 200:
            print(f"   ❌ Study creation failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            raise AssertionError(f"Study creation failed: {response.status_code}")
        
        data = response.json()
        if not data.get("success", False):
            print(f"   ❌ Study creation failed: {data}")
            raise AssertionError(f"Study creation was not successful: {data.get('error', 'Unknown error')}")
        
        assert data["success"] == True
        
        self.created_subject_id = data["subject_id"]
        self.created_series_ids = data["series_ids"]
        self.created_disease_ids = data["disease_ids"]
        
        print(f"   ✅ Study created - Subject: {self.created_subject_id}, Series: {len(self.created_series_ids)}, Diseases: {len(self.created_disease_ids)}")

    async def test_get_patient_imaging_studies(self, client):
        """Test retrieving patient imaging studies."""
        print("🔍 Testing patient imaging studies retrieval...")
        
        response = await client.get(
            f"{BASE_URL}/imaging/patients/{self.test_patient_mrn}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Studies retrieval failed: {response.status_code}"
        data = response.json()
        assert data["success"] == True
        assert data["total_studies"] >= 1
        assert len(data["imaging_studies"]) >= 1
        
        study = data["imaging_studies"][0]
        assert study["subject_name"] == "BraTS20_Validation_004"
        assert study["modality"] == "mri"
        assert len(study["series"]) == 2
        
        print(f"   ✅ Retrieved {data['total_studies']} imaging studies")

    async def test_get_imaging_subject_detail(self, client):
        """Test retrieving specific imaging subject details."""
        print("🔍 Testing imaging subject detail retrieval...")
        
        response = await client.get(
            f"{BASE_URL}/imaging/subjects/{self.created_subject_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Subject detail failed: {response.status_code}"
        data = response.json()
        assert data["success"] == True
        
        subject = data["imaging_subject"]
        assert subject["subject_id"] == self.created_subject_id
        assert subject["subject_name"] == "BraTS20_Validation_004"
        assert len(subject["series"]) == 2
        
        # Check series details
        for series in subject["series"]:
            assert "sequence_type" in series
            assert "file_uri" in series
            assert len(series["diseases"]) >= 0
        
        print("   ✅ Subject details retrieved successfully")

    async def test_get_patient_imaging_summary(self, client):
        """Test patient imaging summary endpoint."""
        print("🔍 Testing patient imaging summary...")
        
        response = await client.get(
            f"{BASE_URL}/imaging/studies/summary/{self.test_patient_mrn}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Summary failed: {response.status_code}"
        data = response.json()
        assert data["success"] == True
        
        summary = data["summary"]
        assert summary["total_studies"] >= 1
        assert summary["total_series"] >= 2
        assert summary["total_diseases"] >= 2
        assert "mri" in summary["modalities"]
        assert "brain" in summary["body_parts"]
        
        print("   ✅ Patient imaging summary retrieved")

    async def test_update_disease_annotation(self, client):
        """Test updating disease annotation."""
        print("🔍 Testing disease annotation update...")
        
        if not self.created_disease_ids:
            print("   ⚠️  No disease IDs to update, skipping...")
            return
        
        disease_id = self.created_disease_ids[0]
        update_data = {
            "confidence_score": 0.95,
            "bounding_box": {
                "x1": 100, "y1": 114, "x2": 140, "y2": 154
            }
        }
        
        response = await client.put(
            f"{BASE_URL}/imaging/annotations/{disease_id}",
            json=update_data,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Disease update failed: {response.status_code}"
        data = response.json()
        assert data["success"] == True
        
        print(f"   ✅ Disease annotation {disease_id} updated")

    async def test_individual_endpoints(self, client):
        """Test individual endpoint functionality."""
        print("🔍 Testing individual endpoints...")
        
        # Test creating subject only
        subject_data = {
            "subject_name": "TEST_SUBJECT_ONLY",
            "patient_mrn": self.test_patient_mrn,
            "modality": "mri",
            "body_part": "brain",
            "study_description": "Test subject creation only"
        }
        
        response = await client.post(
            f"{BASE_URL}/imaging/subjects",
            json=subject_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        test_subject_id = data["subject_id"]
        
        # Test adding series to existing subject
        series_request = {
            "subject_id": test_subject_id,
            "series_data": [
                {
                    "sequence_type": "flair",
                    "file_uri": "https://example.com/test_flair.nii.gz",
                    "image_resolution": "256x256x180"
                }
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/imaging/subjects/{test_subject_id}/series",
            json=series_request,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        test_series_ids = data["series_ids"]
        
        # Test adding disease annotations to existing series
        annotation_request = {
            "series_ids": test_series_ids,
            "disease_data": [
                {
                    "series_index": 0,
                    "bounding_box": {
                        "x1": 50, "y1": 60, "x2": 100, "y2": 110
                    },
                    "confidence_score": 0.75,
                    "class_name": "brain_tumour"
                }
            ]
        }
        
        response = await client.post(
            f"{BASE_URL}/imaging/annotations",
            json=annotation_request,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
        # Clean up the test subject
        await client.delete(
            f"{BASE_URL}/imaging/subjects/{test_subject_id}",
            headers=self.headers
        )
        
        print("   ✅ Individual endpoints tested successfully")

    async def test_error_cases(self, client):
        """Test error handling."""
        print("🔍 Testing error cases...")
        
        # Test unauthorized access
        response = await client.get(f"{BASE_URL}/imaging/patients/{self.test_patient_mrn}")
        assert response.status_code == 401
        
        # Test nonexistent patient
        response = await client.get(
            f"{BASE_URL}/imaging/patients/NONEXISTENT",
            headers=self.headers
        )
        assert response.status_code == 404
        
        # Test nonexistent subject
        response = await client.get(
            f"{BASE_URL}/imaging/subjects/99999",
            headers=self.headers
        )
        assert response.status_code == 404
        
        print("   ✅ Error cases handled correctly")


    async def cleanup_test_environment(self, client):
        """Clean up test data based on what was created."""
        print("🧹 Cleaning up test environment...")
        
        try:
            # Always delete imaging data created during test
            if self.created_subject_id:
                response = await client.delete(
                    f"{BASE_URL}/imaging/subjects/{self.created_subject_id}",
                    headers=self.headers
                )
                if response.status_code == 200:
                    print("   ✅ Imaging data cleaned up")
                else:
                    print(f"   ⚠️  Imaging cleanup warning: {response.status_code}")
        except Exception as e:
            print(f"   ⚠️  Imaging cleanup error: {e}")
        
        # Only cleanup user/patient if WE created them (not if using existing)
        if self.created_user or self.created_patient:
            await self.cleanup_test_user_patient()
        else:
            print("   ✅ Preserving existing user/patient data")

    async def cleanup_test_user_patient(self):
        """Clean up test user and patient if created."""
        if not (self.created_user or self.created_patient):
            print("   No user/patient cleanup needed")
            return
        
        print("   Cleaning up test user and patient...")
        
        try:
            from app.core.db import AsyncSessionLocal, User, Patient, doctor_patient_association
            from sqlalchemy import delete, select
            
            async with AsyncSessionLocal() as db:
                # Import imaging models for cleanup
                from app.core.db.schema import ImagingSubject, ImagingSeries, Disease
                
                # Delete imaging data first (foreign key dependencies)
                if self.created_patient:
                    # Delete diseases first
                    await db.execute(delete(Disease).where(
                        Disease.series_id.in_(
                            select(ImagingSeries.series_id).where(
                                ImagingSeries.subject_id.in_(
                                    select(ImagingSubject.subject_id).where(
                                        ImagingSubject.patient_mrn == self.test_patient_mrn
                                    )
                                )
                            )
                        )
                    ))
                    
                    # Delete series next
                    await db.execute(delete(ImagingSeries).where(
                        ImagingSeries.subject_id.in_(
                            select(ImagingSubject.subject_id).where(
                                ImagingSubject.patient_mrn == self.test_patient_mrn
                            )
                        )
                    ))
                    
                    # Delete subjects
                    await db.execute(delete(ImagingSubject).where(
                        ImagingSubject.patient_mrn == self.test_patient_mrn
                    ))
                
                # Delete relationship data
                await db.execute(delete(doctor_patient_association).where(
                    doctor_patient_association.c.doctor_id == self.test_user_id
                ))
                await db.execute(delete(doctor_patient_association).where(
                    doctor_patient_association.c.patient_mrn == self.test_patient_mrn
                ))
                
                # Delete test patient data
                if self.created_patient:
                    await db.execute(delete(Patient).where(Patient.patient_mrn == self.test_patient_mrn))
                
                # Delete test user data
                if self.created_user:
                    await db.execute(delete(User).where(User.user_id == self.test_user_id))
                
                await db.commit()
                print("   ✅ Test user/patient cleanup completed")
                
        except Exception as e:
            print(f"   ⚠️  User/patient cleanup error: {e}")

    # Utility methods for external use
    async def inject_imaging_data(self, client):
        """Standalone method to inject imaging data - NO AUTO CLEANUP."""
        print("💉 Injecting imaging data...")
        await self.setup_test_environment(client)
        await self.authenticate_user(client)
        await self.test_create_complete_imaging_study(client)
        print(f"   ✅ Imaging data injected - Subject ID: {self.created_subject_id}")
        print("   📌 Data will persist - use delete_imaging_data() to clean up later")
        return self.created_subject_id

    async def delete_imaging_data(self, client):
        """Standalone method to delete imaging data."""
        print("🗑️  Deleting imaging data...")
        if self.created_subject_id and self.headers:
            response = await client.delete(
                f"{BASE_URL}/imaging/subjects/{self.created_subject_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                print("   ✅ Imaging data deleted")
            else:
                print(f"   ⚠️  Delete failed: {response.status_code}")
        
        # Only cleanup user/patient if WE created them
        if self.created_user or self.created_patient:
            await self.cleanup_test_user_patient()
            print("   ✅ Test user/patient also deleted")
        else:
            print("   ✅ Existing user/patient preserved")


async def run_full_test():
    """Run full test suite with new user/patient."""
    print("🔬 Running full imaging API test with new user/patient")
    tester = ImagingAPITester(use_existing_user=False)
    await tester.run_all_tests()


async def run_test_with_existing_user(user_id: str, patient_mrn: str):
    """Run test with existing user and patient."""
    print(f"🔬 Running imaging API test with existing user: {user_id}, patient: {patient_mrn}")
    tester = ImagingAPITester(use_existing_user=True, existing_user_id=user_id, existing_patient_mrn=patient_mrn)
    await tester.run_all_tests()


async def inject_test_data(user_id: Optional[str] = None, patient_mrn: Optional[str] = None):
    """Standalone function to inject test imaging data - DATA PERSISTS."""
    print("💉 Injecting test imaging data...")
    async with httpx.AsyncClient() as client:
        tester = ImagingAPITester(
            use_existing_user=bool(user_id and patient_mrn),
            existing_user_id=user_id,
            existing_patient_mrn=patient_mrn
        )
        subject_id = await tester.inject_imaging_data(client)
        print(f"📌 Subject ID {subject_id} created and will persist")
        print("   Use delete_test_data(tester) to clean up later")
        return subject_id, tester


async def delete_test_data(tester: ImagingAPITester):
    """Standalone function to delete test imaging data."""
    print("🗑️  Deleting test imaging data...")
    async with httpx.AsyncClient() as client:
        await tester.delete_imaging_data(client)


async def delete_injected_data(subject_id: int, user_id: Optional[str] = None, patient_mrn: Optional[str] = None):
    """Delete previously injected imaging data by subject ID."""
    print(f"🗑️  Deleting injected imaging data (Subject ID: {subject_id})...")
    
    async with httpx.AsyncClient() as client:
        # Create tester with the original injection parameters
        tester = ImagingAPITester(
            use_existing_user=bool(user_id and patient_mrn),
            existing_user_id=user_id or "imaging_test_doctor",
            existing_patient_mrn=patient_mrn or "IMG_P12345"
        )
        
        # Set the subject ID and authenticate
        tester.created_subject_id = subject_id
        await tester.authenticate_user(client)
        
        # Delete only the imaging data
        response = await client.delete(
            f"{BASE_URL}/imaging/subjects/{subject_id}",
            headers=tester.headers
        )
        
        if response.status_code == 200:
            print(f"   ✅ Subject {subject_id} and all related data deleted")
        else:
            print(f"   ⚠️  Delete failed: {response.status_code}")
            data = response.json()
            print(f"   Error: {data}")


async def main():
    """Main test runner with options."""
    print("🏥 Imaging API Test Runner")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "existing" and len(sys.argv) >= 4:
            user_id = sys.argv[2]
            patient_mrn = sys.argv[3]
            await run_test_with_existing_user(user_id, patient_mrn)
        elif sys.argv[1] == "inject":
            user_id = sys.argv[2] if len(sys.argv) > 2 else None
            patient_mrn = sys.argv[3] if len(sys.argv) > 3 else None
            subject_id, _ = await inject_test_data(user_id, patient_mrn)
            print(f"✅ Data injected successfully! Subject ID: {subject_id}")
            print(f"💡 To delete later: python test_imaging_api.py delete {subject_id} {user_id or ''} {patient_mrn or ''}")
        elif sys.argv[1] == "delete" and len(sys.argv) >= 3:
            subject_id = int(sys.argv[2])
            user_id = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
            patient_mrn = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
            await delete_injected_data(subject_id, user_id, patient_mrn)
        else:
            print("Usage:")
            print("  python test_imaging_api.py                                         # Full test with new user (auto-cleanup)")
            print("  python test_imaging_api.py existing <user_id> <patient_mrn>        # Test with existing user (preserve user/patient)")
            print("  python test_imaging_api.py inject [user_id] [patient_mrn]          # Inject test data (NO auto-cleanup)")
            print("  python test_imaging_api.py delete <subject_id> [user_id] [patient] # Delete previously injected data")
            print("")
            print("Examples:")
            print("  python test_imaging_api.py inject testdoctor P12345               # Inject with existing user/patient")
            print("  python test_imaging_api.py inject                                  # Inject with new test user/patient")
            print("  python test_imaging_api.py delete 123 testdoctor P12345           # Delete specific subject")
    else:
        await run_full_test()


if __name__ == "__main__":
    try:
        # Check if server is running
        async def check_server():
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{BASE_URL}/server_on", timeout=5.0)
                return response.status_code == 200
        
        if not asyncio.run(check_server()):
            raise Exception("Server not responding")
        
        asyncio.run(main())
        print("\n🎉 Imaging API tests completed successfully!")
        
    except httpx.ConnectError:
        print("❌ Error: Server not running. Please start the server with: python server.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)