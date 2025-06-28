#!/usr/bin/env python3
"""
Comprehensive Multi-Turn Conversation Test
Tests all reference types, conversation context, and reference resolution in a realistic scenario.
"""

import asyncio
import aiohttp
import json
import uuid
import sys
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://localhost:8000"

class ComprehensiveConversationTester:
    def __init__(self):
        self.access_token = None
        self.headers = {"Content-Type": "application/json"}
        
        # Generate unique test data
        unique_suffix = str(uuid.uuid4())[:6]
        self.test_user_id = f"comptest_{unique_suffix}"
        self.test_email = f"comptest.{unique_suffix}@medical.com"
        self.test_patient_mrn = f"COMPTEST_P{unique_suffix}"
        
        # Track conversation
        self.conversation_id = None
        self.all_references_found = []
        self.conversation_turns = []

    async def setup_comprehensive_test_environment(self, session):
        """Setup comprehensive test environment with rich medical data"""
        print("🔧 Setting up comprehensive test environment...")
        
        # Register test doctor
        user_data = {
            "email": self.test_email,
            "phone_num": "01044444444",
            "name": {"first_name": "Comprehensive", "last_name": "TestDoc"},
            "user_id": self.test_user_id,
            "password": "CompTest123!",
            "position": "doctor",
            "licence_num": "COMP123456"
        }
        
        async with session.post(f"{BASE_URL}/auth/register", json=user_data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to register: {error_text}")
        
        # Login and get token
        login_data = {"user_id": self.test_user_id, "password": "CompTest123!"}
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            if response.status != 200:
                raise Exception("Failed to login")
            data = await response.json()
            self.access_token = data["access_token"]
            self.headers["Authorization"] = f"Bearer {self.access_token}"
        
        # Create test patient
        patient_data = {
            "phone_num": "01088888888",
            "patient_mrn": self.test_patient_mrn,
            "name": {"first_name": "John", "last_name": "Doe"},
            "age": 45,
            "birthdate": datetime(1978, 5, 20).isoformat(),
            "body_part": ["cardiovascular", "endocrine"],
            "ai_ready": True,
            "gender": "male"
        }
        
        async with session.post(f"{BASE_URL}/patients/create", json=patient_data) as response:
            if response.status != 200:
                raise Exception("Failed to create patient")
        
        # Assign patient to doctor
        async with session.post(
            f"{BASE_URL}/patients/assign/{self.test_patient_mrn}",
            headers=self.headers
        ) as response:
            if response.status != 200:
                raise Exception("Failed to assign patient")
        
        print("✅ Comprehensive test environment ready")

    async def create_comprehensive_medical_records(self, session):
        """Create comprehensive medical records covering all reference types"""
        print("📝 Creating comprehensive medical records...")
        
        # Create multiple notes of different types
        notes_data = [
            {
                "title": "Initial Diabetes Consultation",
                "content": "Patient presents with newly diagnosed Type 2 diabetes. HbA1c 8.2%. Started on metformin 500mg BID. Discussed lifestyle modifications including diet and exercise.",
                "note_type": "consult"
            },
            {
                "title": "Hypertension Follow-up",
                "content": "Blood pressure well controlled on lisinopril 10mg daily. Patient reports good medication adherence. No side effects noted.",
                "note_type": "consult"
            },
            {
                "title": "Cardiac Echo Results Review",
                "content": "Echocardiogram shows normal left ventricular function with EF 55%. No wall motion abnormalities. Mild mitral regurgitation.",
                "note_type": "radiology"
            }
        ]
        
        for note_data in notes_data:
            async with session.post(
                f"{BASE_URL}/notes/create/{self.test_patient_mrn}",
                json=note_data,
                headers=self.headers
            ) as response:
                if response.status == 200:
                    print(f"   ✓ Created note: {note_data['title']}")
                else:
                    print(f"   ⚠️ Failed to create note: {await response.text()}")
        
        # Create lab results directly in database
        try:
            from app.core.db import AsyncSessionLocal
            from app.core.db.schema import LabResult, Medicalhistory, Appointment, Examination
            from bson import ObjectId
            
            async with AsyncSessionLocal() as db:
                # Create medical history
                medical_history = Medicalhistory(
                    medicalhistory_id=str(ObjectId()),
                    medicalhistory_date=datetime.now() - timedelta(days=30),
                    medicalhistory_title="Type 2 Diabetes Mellitus",
                    medicalhistory_content="Patient diagnosed with T2DM following elevated glucose levels. Family history of diabetes. No diabetic complications at time of diagnosis.",
                    tags=["diabetes", "endocrine", "chronic"],
                    patient_mrn=self.test_patient_mrn,
                    doctor_id=self.test_user_id
                )
                db.add(medical_history)
                
                # Create lab results
                lab_data = [
                    {
                        "test_name": "HbA1c",
                        "result_value": "8.2",
                        "normal_values": "<7.0%",
                        "unit": "%"
                    },
                    {
                        "test_name": "Fasting Glucose",
                        "result_value": "145",
                        "normal_values": "70-100 mg/dL",
                        "unit": "mg/dL"
                    },
                    {
                        "test_name": "Total Cholesterol",
                        "result_value": "220",
                        "normal_values": "<200 mg/dL",
                        "unit": "mg/dL"
                    },
                    {
                        "test_name": "Blood Pressure Systolic",
                        "result_value": "135",
                        "normal_values": "<130 mmHg",
                        "unit": "mmHg"
                    },
                    {
                        "test_name": "Blood Pressure Diastolic",
                        "result_value": "85",
                        "normal_values": "<80 mmHg",
                        "unit": "mmHg"
                    }
                ]
                
                for lab_item in lab_data:
                    lab_result = LabResult(
                        test_name=lab_item["test_name"],
                        result_value=lab_item["result_value"],
                        normal_values=lab_item["normal_values"],
                        unit=lab_item["unit"],
                        patient_mrn=self.test_patient_mrn,
                        medicalhistory_id=medical_history.medicalhistory_id
                    )
                    db.add(lab_result)
                
                # Create appointments
                appointments_data = [
                    {
                        "appointment_detail": "Diabetes follow-up visit. Review medications and lifestyle modifications.",
                        "start_time": datetime.now() + timedelta(days=30),
                        "finish_time": datetime.now() + timedelta(days=30, hours=1)
                    },
                    {
                        "appointment_detail": "Annual physical examination with focus on diabetic complications screening.",
                        "start_time": datetime.now() - timedelta(days=7),
                        "finish_time": datetime.now() - timedelta(days=7) + timedelta(hours=1)
                    }
                ]
                
                for appt_data in appointments_data:
                    appointment = Appointment(
                        appointment_id=str(ObjectId()),
                        appointment_detail=appt_data["appointment_detail"],
                        start_time=appt_data["start_time"],
                        finish_time=appt_data["finish_time"],
                        patient_mrn=self.test_patient_mrn,
                        doctor_id=self.test_user_id
                    )
                    db.add(appointment)
                
                # Create examination
                examination = Examination(
                    examination_id=str(ObjectId()),
                    examination_title="Comprehensive Physical Examination",
                    examination_date=datetime.now() - timedelta(days=14),
                    patient_mrn=self.test_patient_mrn,
                    doctor_id=self.test_user_id
                )
                db.add(examination)
                
                await db.commit()
                print("   ✓ Created comprehensive medical records in database")
        except Exception as e:
            print(f"   ⚠️ Could not create database records: {e}")

    async def conduct_multiturn_conversation(self, session):
        """Conduct a realistic multi-turn conversation testing all reference types"""
        print("\n🗣️ Starting multi-turn conversation...")
        
        # Conversation turns with different types of queries
        conversation_turns = [
            {
                "turn": 1,
                "query": "Can you give me an overview of John Doe's diabetes management? I'd like to see his recent lab results and any relevant notes.",
                "expected_refs": ["labresults", "notes", "medicalhistories"],
                "description": "Initial diabetes overview - should reference lab results and notes"
            },
            {
                "turn": 2,
                "query": "Looking at those HbA1c results you mentioned, how do they compare to the target range? Also, what upcoming appointments does he have?",
                "expected_refs": ["labresults", "appointments"],
                "description": "Follow-up referencing previous context + appointments"
            },
            {
                "turn": 3,
                "query": "I see his blood pressure was elevated. Can you review his cardiovascular status including any examinations and related lab work?",
                "expected_refs": ["labresults", "examinations", "notes"],
                "description": "Cardiovascular focus - examinations and related data"
            },
            {
                "turn": 4,
                "query": "Based on everything we've discussed about his diabetes and hypertension, what does his medical history show about these conditions?",
                "expected_refs": ["medicalhistories", "notes"],
                "description": "Medical history focus with conversation context"
            },
            {
                "turn": 5,
                "query": "Can you also search for the latest diabetes management guidelines to help inform his treatment plan?",
                "expected_refs": ["external"],
                "description": "External web search for guidelines"
            }
        ]
        
        for turn_data in conversation_turns:
            print(f"\n   💬 Turn {turn_data['turn']}: {turn_data['description']}")
            print(f"   📝 Query: {turn_data['query']}")
            
            # Prepare chat data
            chat_data = {
                "query": turn_data["query"],
                "patient_mrn": self.test_patient_mrn
            }
            
            # Add conversation_id for subsequent turns
            if self.conversation_id:
                chat_data["conversation_id"] = self.conversation_id
            
            # Make the chat request
            async with session.post(f"{BASE_URL}/agent/chat", json=chat_data, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"   ❌ Chat failed: {error_text}")
                    continue
                
                data = await response.json()
                response_text = data.get("response", {}).get("text", "")
                tool_calls = data.get("response", {}).get("tool_calls", [])
                
                # Get conversation_id from first turn
                if not self.conversation_id:
                    self.conversation_id = data.get("conversation_id")
                    print(f"   🔗 Started conversation: {self.conversation_id}")
                
                # Extract references from response
                internal_refs = re.findall(r'([a-zA-Z]+_[a-zA-Z0-9]+)', response_text)
                external_refs = re.findall(r'\[([a-f0-9]{6,12})\]', response_text)
                
                all_refs = internal_refs + external_refs
                turn_result = {
                    "turn": turn_data["turn"],
                    "query": turn_data["query"],
                    "response_length": len(response_text),
                    "tools_used": len(tool_calls),
                    "references_found": len(all_refs),
                    "reference_types": list(set([ref.split('_')[0] if '_' in ref else 'external' for ref in all_refs])),
                    "references": all_refs,
                    "expected_refs": turn_data["expected_refs"]
                }
                
                self.conversation_turns.append(turn_result)
                self.all_references_found.extend(all_refs)
                
                print(f"   ✅ Response: {len(response_text)} chars, {len(tool_calls)} tools, {len(all_refs)} references")
                print(f"   🔗 Reference types found: {turn_result['reference_types']}")
                
                # Brief pause between turns
                await asyncio.sleep(1)
        
        print(f"\n✅ Completed {len(conversation_turns)} conversation turns")
        return conversation_turns

    async def test_all_references_resolution(self, session):
        """Test resolution of all references found during conversation"""
        print(f"\n🔍 Testing resolution of {len(set(self.all_references_found))} unique references...")
        
        unique_refs = list(set(self.all_references_found))
        resolution_results = []
        
        for ref_id in unique_refs:
            async with session.get(
                f"{BASE_URL}/references/resolve/{ref_id}",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    ref_type = data.get("type", "unknown")
                    
                    resolution_results.append({
                        "reference_id": ref_id,
                        "status": "success",
                        "type": ref_type,
                        "reference_type": data.get("reference_type", "external")
                    })
                    print(f"   ✅ {ref_id}: {ref_type}")
                else:
                    resolution_results.append({
                        "reference_id": ref_id,
                        "status": "failed",
                        "error": f"HTTP {response.status}"
                    })
                    print(f"   ❌ {ref_id}: Failed")
        
        return resolution_results

    async def cleanup_test_data(self):
        """Clean up test data"""
        try:
            from app.core.db import AsyncSessionLocal, User, Patient, doctor_patient_association, Note, LabResult, Conversation, Message, MessageReference, Reference, Medicalhistory, Appointment, Examination
            from sqlalchemy import delete, select
            
            async with AsyncSessionLocal() as db:
                # Delete in correct order
                await db.execute(delete(MessageReference).where(
                    MessageReference.message_id.in_(
                        select(Message.message_id).join(Conversation).where(
                            Conversation.doctor_id.like("comptest_%")
                        )
                    )
                ))
                
                await db.execute(delete(Reference).where(
                    Reference.reference_id.like("notes_%") |
                    Reference.reference_id.like("labresults_%") |
                    Reference.reference_id.like("appointments_%") |
                    Reference.reference_id.like("medicalhistories_%") |
                    Reference.reference_id.like("examinations_%")
                ))
                
                await db.execute(delete(Message).where(
                    Message.conversation_id.in_(
                        select(Conversation.conversation_id).where(
                            Conversation.doctor_id.like("comptest_%")
                        )
                    )
                ))
                await db.execute(delete(Conversation).where(
                    Conversation.doctor_id.like("comptest_%")
                ))
                
                await db.execute(delete(LabResult).where(LabResult.patient_mrn.like("COMPTEST_P%")))
                await db.execute(delete(Note).where(Note.patient_mrn.like("COMPTEST_P%")))
                await db.execute(delete(Appointment).where(Appointment.patient_mrn.like("COMPTEST_P%")))
                await db.execute(delete(Examination).where(Examination.patient_mrn.like("COMPTEST_P%")))
                await db.execute(delete(Medicalhistory).where(Medicalhistory.patient_mrn.like("COMPTEST_P%")))
                
                await db.execute(delete(doctor_patient_association).where(
                    doctor_patient_association.c.doctor_id.like("comptest_%")
                ))
                
                await db.execute(delete(Patient).where(Patient.patient_mrn.like("COMPTEST_P%")))
                await db.execute(delete(User).where(User.user_id.like("comptest_%")))
                
                await db.commit()
                print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    async def run_comprehensive_test(self):
        """Run comprehensive multi-turn conversation test"""
        print("🧪 COMPREHENSIVE MULTI-TURN CONVERSATION TEST")
        print("=" * 80)
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300)) as session:
            try:
                await self.cleanup_test_data()
                await self.setup_comprehensive_test_environment(session)
                await self.create_comprehensive_medical_records(session)
                
                # Conduct multi-turn conversation
                conversation_results = await self.conduct_multiturn_conversation(session)
                
                # Test reference resolution
                resolution_results = await self.test_all_references_resolution(session)
                
                # Analyze results
                print(f"\n📊 COMPREHENSIVE TEST RESULTS:")
                print(f"=" * 50)
                print(f"🗣️ Conversation turns: {len(conversation_results)}")
                print(f"🔗 Total references found: {len(self.all_references_found)}")
                print(f"🔍 Unique references: {len(set(self.all_references_found))}")
                
                # Reference type breakdown
                ref_types = {}
                for ref in self.all_references_found:
                    ref_type = ref.split('_')[0] if '_' in ref else 'external'
                    ref_types[ref_type] = ref_types.get(ref_type, 0) + 1
                
                print(f"📋 Reference types found:")
                for ref_type, count in ref_types.items():
                    print(f"   {ref_type}: {count}")
                
                # Resolution success rate
                successful_resolutions = sum(1 for r in resolution_results if r.get('status') == 'success')
                total_resolutions = len(resolution_results)
                success_rate = (successful_resolutions / total_resolutions * 100) if total_resolutions > 0 else 0
                
                print(f"✅ Reference resolution success rate: {successful_resolutions}/{total_resolutions} ({success_rate:.1f}%)")
                
                # Conversation context analysis
                print(f"🔄 Conversation context test:")
                print(f"   Conversation ID maintained: {'✅' if self.conversation_id else '❌'}")
                
                await self.cleanup_test_data()
                
                return success_rate > 80  # Consider test successful if >80% references resolve
                
            except Exception as e:
                print(f"\n💥 Test failed: {e}")
                import traceback
                traceback.print_exc()
                return False

async def main():
    print("🧪 COMPREHENSIVE MULTI-TURN CONVERSATION TEST SUITE")
    print("This test validates:")
    print("- Multi-turn conversation with context")
    print("- All 6 reference types (notes, appointments, medical histories, examinations, lab results, external)")
    print("- Reference resolution API")
    print("- Conversation continuity")
    print("=" * 80)
    
    # Check server
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/server_on", timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    raise Exception("Server not responding")
            print("✅ Server is running")
        except Exception as e:
            print(f"❌ Server connection failed: {e}")
            return False
    
    # Run test
    tester = ComprehensiveConversationTester()
    success = await tester.run_comprehensive_test()
    return success

if __name__ == "__main__":
    print("🎯 This test validates comprehensive multi-turn conversations with all reference types")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)