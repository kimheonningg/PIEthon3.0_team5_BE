#!/usr/bin/env python3
import asyncio
import httpx
import json

async def get_api_examples():
    async with httpx.AsyncClient() as client:
        # Login first
        login_data = {
            "user_id": "imaging_test_doctor",
            "password": "imaging_test_password123"
        }
        
        response = await client.post("http://localhost:8000/auth/login", json=login_data)
        if response.status_code != 200:
            print("Login failed")
            return
            
        data = response.json()
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        
        print("=" * 60)
        print("1. GET PATIENT IMAGING STUDIES")
        print("=" * 60)
        print("Endpoint: GET /imaging/patients/{patient_mrn}")
        print()
        
        # Get patient studies
        response = await client.get(
            "http://localhost:8000/imaging/patients/IMG_P12345",
            headers=headers
        )
        
        if response.status_code == 200:
            studies_data = response.json()
            print("Response:")
            print(json.dumps(studies_data, indent=2))
            
            # If we have studies, get detailed series info
            if studies_data.get("imaging_studies") and len(studies_data["imaging_studies"]) > 0:
                subject_id = studies_data["imaging_studies"][0]["subject_id"]
                
                print("\n" + "=" * 60)
                print("2. GET IMAGING SUBJECT DETAIL (Series Info)")
                print("=" * 60)
                print(f"Endpoint: GET /imaging/subjects/{subject_id}")
                print()
                
                response = await client.get(
                    f"http://localhost:8000/imaging/subjects/{subject_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    subject_data = response.json()
                    print("Response:")
                    print(json.dumps(subject_data, indent=2))
                else:
                    print(f"Subject detail failed: {response.status_code}")
                    print(response.text)
            
            print("\n" + "=" * 60)
            print("3. GET PATIENT IMAGING SUMMARY")
            print("=" * 60)
            print("Endpoint: GET /imaging/studies/summary/{patient_mrn}")
            print()
            
            response = await client.get(
                "http://localhost:8000/imaging/studies/summary/IMG_P12345",
                headers=headers
            )
            
            if response.status_code == 200:
                summary_data = response.json()
                print("Response:")
                print(json.dumps(summary_data, indent=2))
            else:
                print(f"Summary failed: {response.status_code}")
                print(response.text)
                
        else:
            print(f"Studies retrieval failed: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(get_api_examples())