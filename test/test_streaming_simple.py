#!/usr/bin/env python3
"""
Simple Streaming Test - Demonstrates streaming with references and tool calls
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

class SimpleStreamingTester:
    def __init__(self):
        self.access_token = None
        self.headers = {"Content-Type": "application/json"}
        
        # Generate unique test data
        unique_suffix = str(uuid.uuid4())[:6]
        self.test_user_id = f"simple_{unique_suffix}"
        self.test_email = f"simple.test.{unique_suffix}@medical.com"
        self.test_patient_mrn = f"SIMPLE_P{unique_suffix}"
        
        # Output files
        self.output_file = OUTPUT_DIR / f"simple_streaming_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.stream_log_file = OUTPUT_DIR / f"simple_stream_chunks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    async def setup_test_environment(self, session):
        """Setup test user and patient with basic medical data"""
        print("🔧 Setting up simple test environment...")
        
        # Register test doctor
        user_data = {
            "email": self.test_email,
            "phone_num": "01055555555",
            "name": {"first_name": "Simple", "last_name": "Tester"},
            "user_id": self.test_user_id,
            "password": "SimpleTest123!",
            "position": "doctor",
            "licence_num": "SMP123456"
        }
        
        async with session.post(f"{BASE_URL}/auth/register", json=user_data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to register: {error_text}")
        
        # Login and get token
        login_data = {"user_id": self.test_user_id, "password": "SimpleTest123!"}
        async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
            if response.status != 200:
                raise Exception("Failed to login")
            data = await response.json()
            self.access_token = data["access_token"]
            self.headers["Authorization"] = f"Bearer {self.access_token}"
        
        # Create test patient
        patient_data = {
            "phone_num": "01011111111",
            "patient_mrn": self.test_patient_mrn,
            "name": {"first_name": "Jane", "last_name": "Test"},
            "age": 35,
            "birthdate": datetime(1988, 3, 15).isoformat(),
            "body_part": ["general"],
            "ai_ready": True,
            "gender": "female"
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
        
        print("✅ Simple test environment ready")

    async def create_basic_medical_data(self, session):
        """Create basic medical data for testing"""
        print("📝 Creating basic medical data...")
        
        # Create a simple medical note
        note_data = {
            "title": "Annual Physical Exam",
            "content": "Patient reports feeling well. Vital signs stable. No acute concerns. Recommend routine follow-up in 6 months.",
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
                    medicalhistory_date=datetime.now() - timedelta(days=60),
                    medicalhistory_title="Hypertension",
                    medicalhistory_content="Patient diagnosed with mild hypertension. Started on lifestyle modifications.",
                    tags=["hypertension", "cardiovascular"],
                    patient_mrn=self.test_patient_mrn,
                    doctor_id=self.test_user_id
                )
                db.add(medical_history)
                
                # Create lab results
                lab_result = LabResult(
                    test_name="Blood Pressure",
                    result_value="140/90",
                    normal_values="<120/80 mmHg",
                    unit="mmHg",
                    patient_mrn=self.test_patient_mrn,
                    medicalhistory_id=medical_history.medicalhistory_id
                )
                db.add(lab_result)
                
                # Create upcoming appointment
                appointment = Appointment(
                    appointment_id=str(ObjectId()),
                    appointment_detail="Follow-up visit for blood pressure monitoring",
                    start_time=datetime.now() + timedelta(days=30),
                    finish_time=datetime.now() + timedelta(days=30, hours=1),
                    patient_mrn=self.test_patient_mrn,
                    doctor_id=self.test_user_id
                )
                db.add(appointment)
                
                await db.commit()
                print("   ✓ Created basic medical records in database")
        except Exception as e:
            print(f"   ⚠️ Could not create database records: {e}")

    async def test_streaming_with_tools_and_references(self, session):
        """Test streaming response that triggers tool calls and generates references"""
        print("\n🌊 Testing streaming with tool calls and references...")
        
        # Query that should trigger medical record tools and web search
        chat_data = {
            "messages": [
                {
                    "role": "user",
                    "content": [{
                        "type": "text", 
                        "text": "Can you review Jane's recent medical records including any lab results and notes? Also search for current hypertension treatment guidelines."
                    }]
                }
            ],
            "patient_mrn": self.test_patient_mrn,
            "system": "You are a medical AI assistant. Always check patient medical records first, then use web search for external guidelines if needed. Cite all sources with reference IDs."
        }
        
        chunk_count = 0
        total_content = ""
        tool_calls_detected = []
        references_found = []
        conversation_id = None
        streaming_data = []
        
        print("🌊 Starting streaming request...")
        
        with open(self.stream_log_file, 'w', encoding='utf-8') as log_file:
            log_file.write(f"SIMPLE STREAMING TEST LOG - {datetime.now().isoformat()}\n")
            log_file.write(f"Question: {chat_data['messages'][0]['content'][0]['text']}\n")
            log_file.write(f"Patient MRN: {self.test_patient_mrn}\n")
            log_file.write("=" * 80 + "\n\n")
            
            async with session.post(f"{BASE_URL}/agent/chat-stream", json=chat_data, headers=self.headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    log_file.write(f"ERROR: Stream failed with status {response.status}\n")
                    log_file.write(f"Error details: {error_text}\n")
                    return {"status": "failed", "error": error_text}
                
                print(f"✅ Stream started successfully")
                log_file.write(f"Stream started successfully - Status: {response.status}\n")
                log_file.write(f"Content-Type: {response.headers.get('content-type', 'unknown')}\n\n")
                
                async for chunk in response.content.iter_chunked(1024):
                    if chunk:
                        chunk_count += 1
                        chunk_text = chunk.decode('utf-8', errors='ignore')
                        total_content += chunk_text
                        
                        # Log chunk details
                        log_file.write(f"CHUNK #{chunk_count:04d} | {len(chunk)} bytes | {datetime.now().strftime('%H:%M:%S.%f')[:-3]}\n")
                        log_file.write("─" * 80 + "\n")
                        log_file.write(chunk_text)
                        log_file.write("\n" + "=" * 80 + "\n\n")
                        log_file.flush()
                        
                        # Analyze chunk for patterns
                        self._analyze_chunk(chunk_text, chunk_count, tool_calls_detected, references_found)
                        
                        # Parse streaming JSON data
                        self._parse_streaming_json(chunk_text, streaming_data)
                        
                        # Look for conversation_id
                        if not conversation_id and "conversation_id" in chunk_text:
                            conversation_id = self._extract_conversation_id(chunk_text)
                        
                        # Show chunk content in real-time (first 100 chars)
                        chunk_preview = chunk_text.replace('\n', ' ').strip()[:100]
                        if chunk_preview:
                            print(f"   📦 Chunk #{chunk_count:03d}: {chunk_preview}{'...' if len(chunk_text) > 100 else ''}")
        
        print(f"🏁 Streaming complete - {chunk_count} chunks, {len(total_content)} characters")
        
        # Analyze final content
        final_analysis = self._analyze_final_content(total_content)
        
        return {
            "status": "success",
            "chunk_count": chunk_count,
            "total_content_length": len(total_content),
            "tool_calls_detected": tool_calls_detected,
            "references_found": references_found,
            "conversation_id": conversation_id,
            "streaming_data": streaming_data,
            "final_analysis": final_analysis,
            "log_file": str(self.stream_log_file)
        }

    def _analyze_chunk(self, chunk_text: str, chunk_num: int, tool_calls_detected: list, references_found: list):
        """Analyze chunk for tool calls and references"""
        
        # Check for tool calls
        if any(tool in chunk_text for tool in ["get_recent_notes", "get_recent_lab", "web_search", "tool_call"]):
            tool_calls_detected.append({
                "chunk": chunk_num,
                "content": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text
            })
        
        # Check for internal references (notes_abc123, labresults_456, etc.)
        internal_refs = re.findall(r'([a-zA-Z]+_[a-zA-Z0-9]+)', chunk_text)
        if internal_refs:
            references_found.extend([{"type": "internal", "ref": ref, "chunk": chunk_num} for ref in internal_refs])
        
        # Check for external references [abc123def]
        external_refs = re.findall(r'\[([a-f0-9]{6,12})\]', chunk_text)
        if external_refs:
            references_found.extend([{"type": "external", "ref": ref, "chunk": chunk_num} for ref in external_refs])

    def _parse_streaming_json(self, chunk_text: str, streaming_data: list):
        """Parse JSON data from streaming chunks"""
        lines = chunk_text.strip().split('\n')
        for line in lines:
            if line.startswith('data: '):
                try:
                    json_data = json.loads(line[6:])
                    streaming_data.append(json_data)
                except json.JSONDecodeError:
                    pass

    def _extract_conversation_id(self, chunk_text: str) -> str:
        """Extract conversation ID from chunk"""
        try:
            lines = chunk_text.split('\n')
            for line in lines:
                if line.startswith('data: '):
                    json_data = json.loads(line[6:])
                    if "conversation_id" in json_data:
                        return json_data["conversation_id"]
        except:
            pass
        return None

    def _analyze_final_content(self, content: str) -> dict:
        """Analyze final content for references and structure"""
        analysis = {
            "internal_references": [],
            "external_references": [],
            "has_sources_section": False,
            "response_structure": {
                "has_medical_records": False,
                "has_external_guidelines": False,
                "total_length": len(content)
            }
        }
        
        # Find internal references
        internal_refs = re.findall(r'([a-zA-Z]+_[a-zA-Z0-9]+)', content)
        analysis["internal_references"] = list(set(internal_refs))
        
        # Find external references
        external_refs = re.findall(r'\[([a-f0-9]{6,12})\]', content)
        analysis["external_references"] = list(set(external_refs))
        
        # Check structure
        analysis["has_sources_section"] = "Sources:" in content or "**Sources:**" in content
        analysis["response_structure"]["has_medical_records"] = any(ref_type in content for ref_type in ["notes_", "labresults_", "appointments_"])
        analysis["response_structure"]["has_external_guidelines"] = len(external_refs) > 0
        
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
                            Conversation.doctor_id.like("simple_%")
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
                            Conversation.doctor_id.like("simple_%")
                        )
                    )
                ))
                await db.execute(delete(Conversation).where(
                    Conversation.doctor_id.like("simple_%")
                ))
                
                # 4. Medical records
                await db.execute(delete(LabResult).where(LabResult.patient_mrn.like("SIMPLE_P%")))
                await db.execute(delete(Note).where(Note.patient_mrn.like("SIMPLE_P%")))
                await db.execute(delete(Appointment).where(Appointment.patient_mrn.like("SIMPLE_P%")))
                await db.execute(delete(Medicalhistory).where(Medicalhistory.patient_mrn.like("SIMPLE_P%")))
                
                # 5. Doctor-patient associations
                await db.execute(delete(doctor_patient_association).where(
                    doctor_patient_association.c.doctor_id.like("simple_%")
                ))
                
                # 6. Patient and user
                await db.execute(delete(Patient).where(Patient.patient_mrn.like("SIMPLE_P%")))
                await db.execute(delete(User).where(User.user_id.like("simple_%")))
                
                await db.commit()
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")

    async def run_test(self):
        """Run the simple streaming test"""
        print("🌊 SIMPLE STREAMING TEST")
        print("=" * 80)
        
        test_results = {
            "test_suite": "simple_streaming_with_references",
            "timestamp": datetime.now().isoformat(),
            "patient_mrn": self.test_patient_mrn,
            "doctor_id": self.test_user_id,
            "output_files": {
                "results": str(self.output_file),
                "stream_log": str(self.stream_log_file)
            }
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            try:
                await self.cleanup_test_data()
                await self.setup_test_environment(session)
                await self.create_basic_medical_data(session)
                
                # Run streaming test
                streaming_result = await self.test_streaming_with_tools_and_references(session)
                test_results["streaming_test"] = streaming_result
                
                # Save results
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(test_results, f, indent=2, ensure_ascii=False)
                
                print(f"\n📄 Results saved to: {self.output_file}")
                print(f"📄 Stream log saved to: {self.stream_log_file}")
                
                # Print summary
                if streaming_result.get("status") == "success":
                    print(f"\n📊 STREAMING TEST SUMMARY:")
                    print(f"✅ Status: Success")
                    print(f"📦 Total chunks: {streaming_result['chunk_count']}")
                    print(f"🔧 Tool calls detected: {len(streaming_result['tool_calls_detected'])}")
                    print(f"🔗 References found: {len(streaming_result['references_found'])}")
                    print(f"📝 Final content length: {streaming_result['total_content_length']} chars")
                    
                    # Reference breakdown
                    internal_refs = [r for r in streaming_result['references_found'] if r['type'] == 'internal']
                    external_refs = [r for r in streaming_result['references_found'] if r['type'] == 'external']
                    print(f"   Internal references: {len(internal_refs)}")
                    print(f"   External references: {len(external_refs)}")
                    
                    analysis = streaming_result['final_analysis']
                    print(f"🔍 Response included medical records: {'✅' if analysis['response_structure']['has_medical_records'] else '❌'}")
                    print(f"🌐 Response included external guidelines: {'✅' if analysis['response_structure']['has_external_guidelines'] else '❌'}")
                else:
                    print(f"❌ Streaming test failed: {streaming_result.get('error')}")
                
                await self.cleanup_test_data()
                return streaming_result.get("status") == "success"
                
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
    print("🌊 SIMPLE STREAMING WITH REFERENCES TEST")
    print("This test demonstrates:")
    print("- Streaming responses with Server-Sent Events")
    print("- Tool calls for medical records and web search")
    print("- Reference generation (internal and external)")
    print("- JSON chunk parsing")
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
    tester = SimpleStreamingTester()
    success = await tester.run_test()
    return success

if __name__ == "__main__":
    print("🎯 This test shows how streaming works with tool calls and references")
    print("   Results and detailed stream logs saved to output/chat/")
    print()
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)