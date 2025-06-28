#!/usr/bin/env python3
"""
Simple Non-Streaming Test - Shows regular /chat endpoint with full response
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
OUTPUT_DIR = Path("output/chat")

class SimpleNonStreamingTester:
    def __init__(self):
        self.access_token = None
        self.headers = {"Content-Type": "application/json"}
        
        # Generate unique test data
        unique_suffix = str(uuid.uuid4())[:6]
        self.test_user_id = f"nonstream_{unique_suffix}"
        self.test_email = f"nonstream.test.{unique_suffix}@medical.com"
        self.test_patient_mrn = f"NONSTREAM_P{unique_suffix}"
        
        # Output files
        self.output_file = OUTPUT_DIR / f"nonstreaming_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    async def setup_test_environment(self, session):
        """Setup test user and patient with basic medical data"""
        print("🔧 Setting up non-streaming test environment...")
        
        # Register test doctor
        user_data = {
            "email": self.test_email,
            "phone_num": "01066666666",
            "name": {"first_name": "NonStream", "last_name": "Tester"},
            "user_id": self.test_user_id,
            "password": "NonStreamTest123!",
            "position": "doctor",
            "licence_num": "NST123456"
        }
        
        async with session.post(f"{BASE_URL}/auth/register", json=user_data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to register: {error_text}")
        
        # Login and get token
        login_data = {"user_id": self.test_user_id, "password": "NonStreamTest123!"}
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            if response.status != 200:
                raise Exception("Failed to login")
            data = await response.json()
            self.access_token = data["access_token"]
            self.headers["Authorization"] = f"Bearer {self.access_token}"
        
        # Create test patient
        patient_data = {
            "phone_num": "01022222222",
            "patient_mrn": self.test_patient_mrn,
            "name": {"first_name": "Bob", "last_name": "TestPatient"},
            "age": 40,
            "birthdate": datetime(1983, 8, 10).isoformat(),
            "body_part": ["general"],
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
        
        print("✅ Non-streaming test environment ready")

    async def create_basic_medical_data(self, session):
        """Create basic medical data for testing"""
        print("📝 Creating basic medical data...")
        
        # Create a simple medical note
        note_data = {
            "title": "Routine Check-up",
            "content": "Patient reports no current symptoms. Physical examination normal. Blood pressure slightly elevated at 140/85. Recommended lifestyle modifications and follow-up in 3 months.",
            "note_type": "consult"
        }
        
        async with session.post(
            f"{BASE_URL}/notes/create/{self.test_patient_mrn}",
            json=note_data,
            headers=self.headers
        ) as response:
            if response.status == 200:
                print("   ✓ Created medical note")
            else:
                print(f"   ⚠️ Failed to create note: {await response.text()}")
        
        # Create lab results in database
        try:
            from app.core.db import AsyncSessionLocal
            from app.core.db.schema import LabResult, Medicalhistory, Appointment
            from bson import ObjectId
            
            async with AsyncSessionLocal() as db:
                # Create medical history
                medical_history = Medicalhistory(
                    medicalhistory_id=str(ObjectId()),
                    medicalhistory_date=datetime.now() - timedelta(days=90),
                    medicalhistory_title="Pre-hypertension",
                    medicalhistory_content="Patient showing early signs of elevated blood pressure. Family history of cardiovascular disease.",
                    tags=["prehypertension", "cardiovascular", "family_history"],
                    patient_mrn=self.test_patient_mrn,
                    doctor_id=self.test_user_id
                )
                db.add(medical_history)
                
                # Create lab results
                lab_results = [
                    {
                        "test_name": "Systolic Blood Pressure",
                        "result_value": "140",
                        "normal_values": "<120 mmHg",
                        "unit": "mmHg"
                    },
                    {
                        "test_name": "Diastolic Blood Pressure",
                        "result_value": "85",
                        "normal_values": "<80 mmHg",
                        "unit": "mmHg"
                    },
                    {
                        "test_name": "LDL Cholesterol",
                        "result_value": "130",
                        "normal_values": "<100 mg/dL",
                        "unit": "mg/dL"
                    }
                ]
                
                for lab_data in lab_results:
                    lab_result = LabResult(
                        test_name=lab_data["test_name"],
                        result_value=lab_data["result_value"],
                        normal_values=lab_data["normal_values"],
                        unit=lab_data["unit"],
                        patient_mrn=self.test_patient_mrn,
                        medicalhistory_id=medical_history.medicalhistory_id
                    )
                    db.add(lab_result)
                
                # Create upcoming appointment
                appointment = Appointment(
                    appointment_id=str(ObjectId()),
                    appointment_detail="Follow-up appointment for blood pressure monitoring and lifestyle counseling",
                    start_time=datetime.now() + timedelta(days=90),
                    finish_time=datetime.now() + timedelta(days=90, hours=1),
                    patient_mrn=self.test_patient_mrn,
                    doctor_id=self.test_user_id
                )
                db.add(appointment)
                
                await db.commit()
                print("   ✓ Created basic medical records in database")
        except Exception as e:
            print(f"   ⚠️ Could not create database records: {e}")

    async def test_non_streaming_chat(self, session):
        """Test regular /chat endpoint (non-streaming)"""
        print("\n💬 Testing non-streaming chat with tool calls and references...")
        
        # Same query as streaming version for comparison
        chat_data = {
            "query": "Can you review Bob's recent medical records including any lab results and notes? Also search for current hypertension treatment guidelines.",
            "patient_mrn": self.test_patient_mrn
        }
        
        print("📡 Sending non-streaming request...")
        start_time = datetime.now()
        
        async with session.post(f"{BASE_URL}/agent/chat", json=chat_data, headers=self.headers) as response:
            if response.status != 200:
                error_text = await response.text()
                return {"status": "failed", "error": error_text}
            
            response_data = await response.json()
            end_time = datetime.now()
            
            # Extract response components
            response_text = response_data.get("response", {}).get("text", "")
            tool_calls = response_data.get("response", {}).get("tool_calls", [])
            conversation_id = response_data.get("conversation_id")
            
            # Analyze response
            response_analysis = self._analyze_response(response_text, tool_calls)
            
            print(f"✅ Non-streaming complete")
            print(f"⏱️  Response time: {(end_time - start_time).total_seconds():.2f} seconds")
            print(f"📝 Response length: {len(response_text)} characters")
            print(f"🔧 Tool calls: {len(tool_calls)}")
            print(f"🔗 References found: {len(response_analysis['all_references'])}")
            
            # Show response preview
            print(f"\n📄 RESPONSE PREVIEW:")
            print("=" * 80)
            response_preview = response_text[:500] + "..." if len(response_text) > 500 else response_text
            print(response_preview)
            print("=" * 80)
            
            # Show tool calls details
            if tool_calls:
                print(f"\n🔧 TOOL CALLS DETAILS:")
                for i, tool_call in enumerate(tool_calls, 1):
                    tool_name = tool_call.get("name", "unknown")
                    tool_args = tool_call.get("args", {})
                    tool_result = tool_call.get("result", "")
                    print(f"   {i}. {tool_name}")
                    if isinstance(tool_args, str):
                        try:
                            import json
                            tool_args = json.loads(tool_args)
                        except:
                            pass
                    if isinstance(tool_args, dict):
                        for key, value in tool_args.items():
                            print(f"      {key}: {value}")
                    
                    # Show result status
                    if "error" in str(tool_result).lower():
                        print(f"      ❌ Result: ERROR")
                    elif tool_result:
                        print(f"      ✅ Result: Success ({len(str(tool_result))} chars)")
                    else:
                        print(f"      ⚠️  Result: Empty")
                    print()
            
            # Show references found
            print(f"\n🔗 REFERENCES ANALYSIS:")
            if response_analysis['all_references']:
                print(f"References found:")
                for ref_type, refs in response_analysis['references_by_type'].items():
                    if refs:
                        print(f"   {ref_type}: {refs}")
            else:
                print("No references found in response")
                # Debug: show what we're looking for
                print("Debug - checking for patterns in response:")
                internal_pattern = r'([a-zA-Z]+_[a-zA-Z0-9]+)'
                external_pattern = r'\[([a-zA-Z0-9]{6,12})\]'
                bracket_pattern = r'\[([^\]]+)\]'
                
                print(f"   Looking for internal refs (type_id): {bool(re.findall(internal_pattern, response_text))}")
                print(f"   Looking for external refs [hash]: {bool(re.findall(external_pattern, response_text))}")
                # Show sample of response to check
                if "[" in response_text:
                    bracket_matches = re.findall(bracket_pattern, response_text)
                    print(f"   Found brackets with content: {bracket_matches[:5]}")  # Show first 5
            
            return {
                "status": "success",
                "response_time_seconds": (end_time - start_time).total_seconds(),
                "response_length": len(response_text),
                "tool_calls_count": len(tool_calls),
                "conversation_id": conversation_id,
                "response_analysis": response_analysis,
                "full_response": response_text,
                "tool_calls": tool_calls,
                "response_data": response_data
            }

    def _analyze_response(self, response_text: str, tool_calls: list) -> dict:
        """Analyze the complete response for references and structure"""
        analysis = {
            "internal_references": [],
            "external_references": [],
            "all_references": [],
            "references_by_type": {},
            "has_sources_section": False,
            "tool_calls_summary": [],
            "response_structure": {
                "has_medical_records": False,
                "has_external_guidelines": False,
                "total_length": len(response_text)
            }
        }
        
        # Find internal references (notes_abc123, labresults_456, etc.)
        internal_refs = re.findall(r'([a-zA-Z]+_[a-zA-Z0-9]+)', response_text)
        analysis["internal_references"] = list(set(internal_refs))
        
        # Find external references [abc123def] - allow alphanumeric, not just hex
        external_refs = re.findall(r'\[([a-zA-Z0-9]{6,12})\]', response_text)
        analysis["external_references"] = list(set(external_refs))
        
        # Combine all references
        analysis["all_references"] = analysis["internal_references"] + analysis["external_references"]
        
        # Group references by type
        ref_types = {}
        for ref in analysis["internal_references"]:
            ref_type = ref.split('_')[0] if '_' in ref else 'unknown'
            if ref_type not in ref_types:
                ref_types[ref_type] = []
            ref_types[ref_type].append(ref)
        if analysis["external_references"]:
            ref_types["external"] = analysis["external_references"]
        analysis["references_by_type"] = ref_types
        
        # Check response structure
        analysis["has_sources_section"] = "Sources:" in response_text or "**Sources:**" in response_text
        analysis["response_structure"]["has_medical_records"] = any(ref_type in response_text for ref_type in ["notes_", "labresults_", "appointments_"])
        analysis["response_structure"]["has_external_guidelines"] = len(external_refs) > 0
        
        # Analyze tool calls
        for tool_call in tool_calls:
            analysis["tool_calls_summary"].append({
                "name": tool_call.get("name", "unknown"),
                "args_count": len(tool_call.get("args", {})),
                "has_result": bool(tool_call.get("result"))
            })
        
        return analysis

    async def cleanup_test_data(self):
        """Clean up test data"""
        try:
            from app.core.db import AsyncSessionLocal, User, Patient, doctor_patient_association, Note, LabResult, Conversation, Message, MessageReference, Reference, Medicalhistory, Appointment
            from sqlalchemy import delete, select
            
            async with AsyncSessionLocal() as db:
                # Delete in correct order to avoid foreign key violations
                # 1. Message references
                await db.execute(delete(MessageReference).where(
                    MessageReference.message_id.in_(
                        select(Message.message_id).join(Conversation).where(
                            Conversation.doctor_id.like("nonstream_%")
                        )
                    )
                ))
                
                # 2. References
                await db.execute(delete(Reference).where(
                    Reference.reference_id.like("notes_%") |
                    Reference.reference_id.like("labresults_%") |
                    Reference.reference_id.like("appointments_%") |
                    Reference.reference_id.like("medicalhistories_%")
                ))
                
                # 3. Messages and conversations
                await db.execute(delete(Message).where(
                    Message.conversation_id.in_(
                        select(Conversation.conversation_id).where(
                            Conversation.doctor_id.like("nonstream_%")
                        )
                    )
                ))
                await db.execute(delete(Conversation).where(
                    Conversation.doctor_id.like("nonstream_%")
                ))
                
                # 4. Medical records
                await db.execute(delete(LabResult).where(LabResult.patient_mrn.like("NONSTREAM_P%")))
                await db.execute(delete(Note).where(Note.patient_mrn.like("NONSTREAM_P%")))
                await db.execute(delete(Appointment).where(Appointment.patient_mrn.like("NONSTREAM_P%")))
                await db.execute(delete(Medicalhistory).where(Medicalhistory.patient_mrn.like("NONSTREAM_P%")))
                
                # 5. Doctor-patient associations
                await db.execute(delete(doctor_patient_association).where(
                    doctor_patient_association.c.doctor_id.like("nonstream_%")
                ))
                
                # 6. Patient and user
                await db.execute(delete(Patient).where(Patient.patient_mrn.like("NONSTREAM_P%")))
                await db.execute(delete(User).where(User.user_id.like("nonstream_%")))
                
                await db.commit()
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    async def run_test(self):
        """Run the non-streaming test"""
        print("💬 NON-STREAMING CHAT TEST")
        print("=" * 80)
        
        test_results = {
            "test_suite": "non_streaming_with_references",
            "timestamp": datetime.now().isoformat(),
            "patient_mrn": self.test_patient_mrn,
            "doctor_id": self.test_user_id,
            "output_files": {
                "results": str(self.output_file)
            }
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            try:
                await self.cleanup_test_data()
                await self.setup_test_environment(session)
                await self.create_basic_medical_data(session)
                
                # Run non-streaming test
                chat_result = await self.test_non_streaming_chat(session)
                test_results["chat_test"] = chat_result
                
                # Save results
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(test_results, f, indent=2, ensure_ascii=False)
                
                print(f"\n📄 Results saved to: {self.output_file}")
                
                # Print summary
                if chat_result.get("status") == "success":
                    print(f"\n📊 NON-STREAMING TEST SUMMARY:")
                    print(f"✅ Status: Success")
                    print(f"⏱️  Response time: {chat_result['response_time_seconds']:.2f} seconds")
                    print(f"📝 Response length: {chat_result['response_length']} characters")
                    print(f"🔧 Tool calls: {chat_result['tool_calls_count']}")
                    print(f"🔗 References found: {len(chat_result['response_analysis']['all_references'])}")
                    
                    # Reference breakdown
                    analysis = chat_result['response_analysis']
                    print(f"   Internal references: {len(analysis['internal_references'])}")
                    print(f"   External references: {len(analysis['external_references'])}")
                    
                    print(f"🔍 Response included medical records: {'✅' if analysis['response_structure']['has_medical_records'] else '❌'}")
                    print(f"🌐 Response included external guidelines: {'✅' if analysis['response_structure']['has_external_guidelines'] else '❌'}")
                else:
                    print(f"❌ Non-streaming test failed: {chat_result.get('error')}")
                
                await self.cleanup_test_data()
                return chat_result.get("status") == "success"
                
            except Exception as e:
                print(f"\n💥 Test failed: {e}")
                import traceback
                traceback.print_exc()
                
                test_results["error"] = str(e)
                test_results["traceback"] = traceback.format_exc()
                
                # Save error results
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(test_results, f, indent=2, ensure_ascii=False)
                
                return False

async def main():
    print("💬 NON-STREAMING CHAT WITH REFERENCES TEST")
    print("This test demonstrates:")
    print("- Regular /chat endpoint (non-streaming)")
    print("- Complete response in single request")
    print("- Tool calls for medical records and web search")
    print("- Reference generation analysis")
    print("- Response structure breakdown")
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
    tester = SimpleNonStreamingTester()
    success = await tester.run_test()
    return success

if __name__ == "__main__":
    print("🎯 This test shows the regular /chat endpoint with complete response analysis")
    print("   Compare with test_streaming_simple.py to see streaming vs non-streaming")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)