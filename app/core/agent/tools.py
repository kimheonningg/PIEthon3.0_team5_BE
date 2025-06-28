from typing import Optional, Dict, Any, List
from langchain_core.tools import tool
from uuid import UUID
from pydantic import BaseModel, Field
from langchain_perplexity import ChatPerplexity
import os
import re
import hashlib
# Add your other imports here
# from app.service.your_service import your_data_functions

# =============================================================================
# GENERAL TOOLS (No user context needed)
# =============================================================================

@tool(description="Search the web for general information. Use this for general knowledge questions that require external information.")
async def web_search(
    query: str = Field(..., description="Search query for general information")
) -> str:
    """
    Search the web for general information using Perplexity.
    Use this for general knowledge questions that don't require user-specific data.
    
    Args:
        query: Search query for general information
        
    Returns:
        Search results from the web
    """
    try:
        # Get API key from environment
        pplx_api_key = os.getenv("PPLX_API_KEY")
        if not pplx_api_key:
            return "Perplexity API key not configured."
        
        # Create Perplexity client
        perplexity = ChatPerplexity(
            pplx_api_key=pplx_api_key,
            model="sonar",
            temperature=0.7
        )
        
        # Format the query for your domain
        enhanced_query = f"Provide a concise, factual response about: {query}"
        
        # Create system message for your domain
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant providing factual information. Keep your responses informative, educational, and concise."
            },
            {"role": "user", "content": enhanced_query}
        ]
        
        # Invoke Perplexity
        response = await perplexity.ainvoke(messages)
        content = response.content
        
        # Extract citations and convert to hash references
        citations = []
        
        # First check for citations in additional_kwargs (primary method)
        if hasattr(response, 'additional_kwargs') and response.additional_kwargs and 'citations' in response.additional_kwargs:
            citations = response.additional_kwargs['citations']
        else:
            # Fallback: try to extract from Sources section in content  
            sources_match = re.search(r'\*\*Sources:\*\*\n(.*?)(?:\n\n|$)', content, re.DOTALL)
            if sources_match:
                sources_text = sources_match.group(1)
                for line in sources_text.split('\n'):
                    line = line.strip()
                    if line:
                        url_match = re.search(r'\[(\d+)\]\s+(.+)', line)
                        if url_match:
                            url = url_match.group(2).strip()
                            if url.startswith('http'):
                                citations.append(url)
        
        # Process citations: strip them from content and create clean sources section
        if citations:
            from app.service.postgres.reference_manager import generate_reference_hash
            
            # Remove ALL numbered citations from content to avoid LLM confusion
            clean_content = re.sub(r'\[(\d+)\]', '', content)
            
            # Create hash references for sources
            hash_references = []
            for citation_url in citations:
                hash_ref = generate_reference_hash(citation_url)
                hash_references.append(hash_ref)
            
            # Append clean sources section with hash references
            if hash_references:
                sources_section = "\n\nSources: " + " ".join(f"[{hash_ref}]" for hash_ref in hash_references)
                content = clean_content + sources_section
            else:
                content = clean_content

        return content
    except Exception as e:
        return f"Error searching the web: {str(e)}"

@tool(description="Get general information or statistics that don't require user context.")
async def get_general_info(
    info_type: str = Field(..., description="Type of information to retrieve"),
    limit: int = Field(10, description="Maximum number of results to return"),
    db = Field(..., description="Database session (injected by tool factory)")
) -> Dict[str, Any]:
    """
    Get general information that doesn't require user-specific context.
    
    Args:
        info_type: Type of information to retrieve
        limit: Maximum number of results
        db: Database session passed from router
        
    Returns:
        Dictionary with the requested information
    """
    try:
        if not db:
            return {"error": "Database connection not available"}
        
        # Your query logic - no user context needed
        # results = await get_general_data(db, info_type, limit)
        
        return {
            "info_type": info_type,
            "results": [],  # Your actual results here
            "count": 0
        }
    except Exception as e:
        return {"error": f"Failed to retrieve information: {str(e)}"}

# =============================================================================
# PATIENT MEDICAL RECORD TOOLS (Require user and patient context)
# =============================================================================

@tool(description="Get recent medical notes for the patient. Use this to find clinical notes, consultation records, treatment notes, and other documented observations.")
async def get_recent_notes(
    limit: int = Field(5, description="Maximum number of recent notes to return (default 5)"),
    note_type: Optional[str] = Field(None, description="Filter by note type: 'consult', 'treatment', 'radiology', 'other'"),
    user = Field(..., description="Current user object (injected by tool factory)"),
    db = Field(..., description="Database session (injected by tool factory)"),
    patient_mrn: str = Field(..., description="Patient MRN for context (injected by tool factory)")
) -> Dict[str, Any]:
    """
    Retrieve recent medical notes for the patient.
    
    Returns notes with reference IDs that can be cited in responses.
    """
    if not db:
        return {"error": "Database connection not available"}
    
    try:
        from app.core.db.schema import Note
        from sqlalchemy import select, desc
        
        # Build query for patient's notes
        query = select(Note).where(
            Note.patient_mrn == patient_mrn,
            Note.deleted == False
        ).order_by(desc(Note.created_at)).limit(limit)
        
        # Add note type filter if specified
        if note_type:
            query = query.where(Note.note_type == note_type)
        
        result = await db.execute(query)
        notes = result.scalars().all()
        
        # Format notes with reference IDs
        formatted_notes = []
        for note in notes:
            reference_id = f"notes_{note.note_id}"
            formatted_notes.append({
                "reference_id": reference_id,
                "title": note.title,
                "content": note.content[:500] + "..." if len(note.content) > 500 else note.content,
                "note_type": note.note_type,
                "created_at": note.created_at.isoformat(),
                "last_modified": note.last_modified.isoformat(),
                "doctor_id": note.doctor_id
            })
        
        return {
            "record_type": "notes",
            "patient_mrn": patient_mrn,
            "filter_applied": note_type,
            "notes": formatted_notes,
            "count": len(formatted_notes),
            "reference_instruction": "Use reference_id in square brackets to cite these notes, e.g., [notes_abc123]"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve notes: {str(e)}"}

@tool(description="Get recent appointments for the patient. Use this to find scheduled visits, appointment details, and visit history.")
async def get_recent_appointments(
    limit: int = Field(5, description="Maximum number of recent appointments to return (default 5)"),
    future_only: bool = Field(False, description="If True, only return future appointments; if False, return recent past and future"),
    user = Field(..., description="Current user object (injected by tool factory)"),
    db = Field(..., description="Database session (injected by tool factory)"),
    patient_mrn: str = Field(..., description="Patient MRN for context (injected by tool factory)")
) -> Dict[str, Any]:
    """
    Retrieve recent appointments for the patient.
    
    Returns appointments with reference IDs that can be cited in responses.
    """
    if not db:
        return {"error": "Database connection not available"}
    
    try:
        from app.core.db.schema import Appointment
        from sqlalchemy import select, desc
        from datetime import datetime
        
        # Build query for patient's appointments
        query = select(Appointment).where(
            Appointment.patient_mrn == patient_mrn
        )
        
        if future_only:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            query = query.where(Appointment.start_time >= now).order_by(Appointment.start_time)
        else:
            query = query.order_by(desc(Appointment.start_time))
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        appointments = result.scalars().all()
        
        # Format appointments with reference IDs
        formatted_appointments = []
        for appointment in appointments:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            reference_id = f"appointments_{appointment.appointment_id}"
            formatted_appointments.append({
                "reference_id": reference_id,
                "appointment_detail": appointment.appointment_detail,
                "start_time": appointment.start_time.isoformat(),
                "finish_time": appointment.finish_time.isoformat(),
                "doctor_id": appointment.doctor_id,
                "is_future": appointment.start_time > now
            })
        
        return {
            "record_type": "appointments",
            "patient_mrn": patient_mrn,
            "filter_applied": "future_only" if future_only else "all_recent",
            "appointments": formatted_appointments,
            "count": len(formatted_appointments),
            "reference_instruction": "Use reference_id in square brackets to cite these appointments, e.g., [appointments_def456]"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve appointments: {str(e)}"}

@tool(description="Get recent medical history entries for the patient. Use this to find past medical conditions, treatments, surgeries, and historical health information.")
async def get_recent_medical_histories(
    limit: int = Field(5, description="Maximum number of recent medical history entries to return (default 5)"),
    tag_filter: Optional[str] = Field(None, description="Filter by tag (e.g., 'diabetes', 'surgery', 'allergy')"),
    user = Field(..., description="Current user object (injected by tool factory)"),
    db = Field(..., description="Database session (injected by tool factory)"),
    patient_mrn: str = Field(..., description="Patient MRN for context (injected by tool factory)")
) -> Dict[str, Any]:
    """
    Retrieve recent medical history entries for the patient.
    
    Returns medical histories with reference IDs that can be cited in responses.
    """
    if not db:
        return {"error": "Database connection not available"}
    
    try:
        from app.core.db.schema import Medicalhistory
        from sqlalchemy import select, desc
        
        # Build query for patient's medical histories
        query = select(Medicalhistory).where(
            Medicalhistory.patient_mrn == patient_mrn
        ).order_by(desc(Medicalhistory.medicalhistory_date)).limit(limit)
        
        result = await db.execute(query)
        histories = result.scalars().all()
        
        # Format medical histories with reference IDs and apply tag filter if needed
        formatted_histories = []
        for history in histories:
            # Apply tag filter if specified
            if tag_filter and history.tags:
                if not any(tag_filter.lower() in tag.lower() for tag in history.tags):
                    continue
            
            reference_id = f"medicalhistories_{history.medicalhistory_id}"
            formatted_histories.append({
                "reference_id": reference_id,
                "title": history.medicalhistory_title,
                "content": history.medicalhistory_content[:500] + "..." if len(history.medicalhistory_content) > 500 else history.medicalhistory_content,
                "date": history.medicalhistory_date.isoformat(),
                "tags": history.tags or [],
                "doctor_id": history.doctor_id
            })
        
        return {
            "record_type": "medical_histories",
            "patient_mrn": patient_mrn,
            "filter_applied": tag_filter,
            "medical_histories": formatted_histories,
            "count": len(formatted_histories),
            "reference_instruction": "Use reference_id in square brackets to cite these medical histories, e.g., [medicalhistories_ghi789]"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve medical histories: {str(e)}"}

@tool(description="Get recent examinations for the patient. Use this to find imaging studies, diagnostic tests, physical examinations, and clinical assessments.")
async def get_recent_examinations(
    limit: int = Field(5, description="Maximum number of recent examinations to return (default 5)"),
    user = Field(..., description="Current user object (injected by tool factory)"),
    db = Field(..., description="Database session (injected by tool factory)"),
    patient_mrn: str = Field(..., description="Patient MRN for context (injected by tool factory)")
) -> Dict[str, Any]:
    """
    Retrieve recent examinations for the patient.
    
    Returns examinations with reference IDs that can be cited in responses.
    """
    if not db:
        return {"error": "Database connection not available"}
    
    try:
        from app.core.db.schema import Examination
        from sqlalchemy import select, desc
        
        # Build query for patient's examinations
        query = select(Examination).where(
            Examination.patient_mrn == patient_mrn
        ).order_by(desc(Examination.examination_date)).limit(limit)
        
        result = await db.execute(query)
        examinations = result.scalars().all()
        
        # Format examinations with reference IDs
        formatted_examinations = []
        for examination in examinations:
            reference_id = f"examinations_{examination.examination_id}"
            formatted_examinations.append({
                "reference_id": reference_id,
                "title": examination.examination_title,
                "examination_date": examination.examination_date.isoformat(),
                "doctor_id": examination.doctor_id
            })
        
        return {
            "record_type": "examinations",
            "patient_mrn": patient_mrn,
            "examinations": formatted_examinations,
            "count": len(formatted_examinations),
            "reference_instruction": "Use reference_id in square brackets to cite these examinations, e.g., [examinations_jkl012]"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve examinations: {str(e)}"}

@tool(description="Get recent lab results for the patient. Use this to find blood tests, lab values, diagnostic markers, and test results with normal ranges.")
async def get_recent_lab_results(
    limit: int = Field(10, description="Maximum number of recent lab results to return (default 10)"),
    test_name_filter: Optional[str] = Field(None, description="Filter by test name (e.g., 'glucose', 'hemoglobin', 'cholesterol')"),
    user = Field(..., description="Current user object (injected by tool factory)"),
    db = Field(..., description="Database session (injected by tool factory)"),
    patient_mrn: str = Field(..., description="Patient MRN for context (injected by tool factory)")
) -> Dict[str, Any]:
    """
    Retrieve recent lab results for the patient.
    
    Returns lab results with reference IDs that can be cited in responses.
    """
    if not db:
        return {"error": "Database connection not available"}
    
    try:
        from app.core.db.schema import LabResult
        from sqlalchemy import select, desc
        
        # Build query for patient's lab results
        query = select(LabResult).where(
            LabResult.patient_mrn == patient_mrn
        ).order_by(desc(LabResult.lab_date)).limit(limit)
        
        # Add test name filter if specified
        if test_name_filter:
            query = query.where(LabResult.test_name.ilike(f"%{test_name_filter}%"))
        
        result = await db.execute(query)
        lab_results = result.scalars().all()
        
        # Format lab results with reference IDs
        formatted_results = []
        for lab_result in lab_results:
            reference_id = f"labresults_{lab_result.lab_result_id}"
            formatted_results.append({
                "reference_id": reference_id,
                "test_name": lab_result.test_name,
                "result_value": lab_result.result_value,
                "normal_values": lab_result.normal_values,
                "unit": lab_result.unit,
                "lab_date": lab_result.lab_date.isoformat(),
                "medicalhistory_id": lab_result.medicalhistory_id
            })
        
        return {
            "record_type": "lab_results",
            "patient_mrn": patient_mrn,
            "filter_applied": test_name_filter,
            "lab_results": formatted_results,
            "count": len(formatted_results),
            "reference_instruction": "Use reference_id in square brackets to cite these lab results, e.g., [labresults_123]"
        }
    except Exception as e:
        return {"error": f"Failed to retrieve lab results: {str(e)}"}

# =============================================================================
# TOOL FACTORY FUNCTION
# =============================================================================

def create_tools_with_user_context(db, user, patient_mrn: Optional[str] = None) -> List:
    """
    Create tool instances with user, db, and patient_mrn pre-bound as default parameters.
    This creates proper tool wrappers that LangGraph can use.
    
    Args:
        user: Current user object from router (e.g., from get_current_user dependency)
        db: Database session from router (e.g., from get_db dependency)
        patient_mrn: Optional patient Medical Record Number for patient-specific context
    """
    
    @tool(description="Get general information or statistics that don't require user context.")
    async def get_general_info_with_context(
        info_type: str = Field(description="Type of information to retrieve"),
        limit: int = Field(default=10, description="Maximum number of results to return")
    ) -> Dict[str, Any]:
        # Set defaults if not provided
        if limit is None:
            limit = 10
        return await get_general_info(info_type, limit, db)
    
    # Medical record tools with context
    @tool(description="Get recent medical notes for the patient. Use this to find clinical notes, consultation records, treatment notes, and other documented observations.")
    async def get_recent_notes_with_context(
        limit: int = Field(default=5, description="Maximum number of recent notes to return (default 5)"),
        note_type: Optional[str] = Field(default=None, description="Filter by note type: 'consult', 'treatment', 'radiology', 'other'")
    ) -> Dict[str, Any]:
        if not db:
            return {"error": "Database connection not available"}
        
        try:
            from app.core.db.schema import Note
            from sqlalchemy import select, desc
            
            # Build query for patient's notes
            query = select(Note).where(
                Note.patient_mrn == patient_mrn,
                Note.deleted == False
            ).order_by(desc(Note.created_at)).limit(limit)
            
            # Add note type filter if specified
            if note_type:
                query = query.where(Note.note_type == note_type)
            
            result = await db.execute(query)
            notes = result.scalars().all()
            
            # Format notes with reference IDs
            formatted_notes = []
            for note in notes:
                reference_id = f"notes_{note.note_id}"
                formatted_notes.append({
                    "reference_id": reference_id,
                    "title": note.title,
                    "content": note.content[:500] + "..." if len(note.content) > 500 else note.content,
                    "note_type": note.note_type,
                    "created_at": note.created_at.isoformat(),
                    "last_modified": note.last_modified.isoformat(),
                    "doctor_id": note.doctor_id
                })
            
            return {
                "record_type": "notes",
                "patient_mrn": patient_mrn,
                "filter_applied": note_type,
                "notes": formatted_notes,
                "count": len(formatted_notes),
                "reference_instruction": "Use reference_id in square brackets to cite these notes, e.g., [notes_abc123]"
            }
        except Exception as e:
            return {"error": f"Failed to retrieve notes: {str(e)}"}
    
    @tool(description="Get recent appointments for the patient. Use this to find scheduled visits, appointment details, and visit history.")
    async def get_recent_appointments_with_context(
        limit: int = Field(default=5, description="Maximum number of recent appointments to return (default 5)"),
        future_only: bool = Field(default=False, description="If True, only return future appointments; if False, return recent past and future")
    ) -> Dict[str, Any]:
        if not db:
            return {"error": "Database connection not available"}
        
        try:
            from app.core.db.schema import Appointment
            from sqlalchemy import select, desc
            from datetime import datetime
            
            # Build query for patient's appointments
            query = select(Appointment).where(
                Appointment.patient_mrn == patient_mrn
            )
            
            if future_only:
                now = datetime.now()  # Use naive datetime to match database
                query = query.where(Appointment.start_time >= now).order_by(Appointment.start_time)
            else:
                query = query.order_by(desc(Appointment.start_time))
            
            query = query.limit(limit)
            
            result = await db.execute(query)
            appointments = result.scalars().all()
            
            # Format appointments with reference IDs
            formatted_appointments = []
            for appointment in appointments:
                now = datetime.now()  # Use naive datetime to match database
                reference_id = f"appointments_{appointment.appointment_id}"
                formatted_appointments.append({
                    "reference_id": reference_id,
                    "appointment_detail": appointment.appointment_detail,
                    "start_time": appointment.start_time.isoformat(),
                    "finish_time": appointment.finish_time.isoformat(),
                    "doctor_id": appointment.doctor_id,
                    "is_future": appointment.start_time > now
                })
            
            return {
                "record_type": "appointments",
                "patient_mrn": patient_mrn,
                "filter_applied": "future_only" if future_only else "all_recent",
                "appointments": formatted_appointments,
                "count": len(formatted_appointments),
                "reference_instruction": "Use reference_id in square brackets to cite these appointments, e.g., [appointments_def456]"
            }
        except Exception as e:
            return {"error": f"Failed to retrieve appointments: {str(e)}"}
    
    @tool(description="Get recent medical history entries for the patient. Use this to find past medical conditions, treatments, surgeries, and historical health information.")
    async def get_recent_medical_histories_with_context(
        limit: int = Field(default=5, description="Maximum number of recent medical history entries to return (default 5)"),
        tag_filter: Optional[str] = Field(default=None, description="Filter by tag (e.g., 'diabetes', 'surgery', 'allergy')")
    ) -> Dict[str, Any]:
        if not db:
            return {"error": "Database connection not available"}
        
        try:
            from app.core.db.schema import Medicalhistory
            from sqlalchemy import select, desc
            
            # Build query for patient's medical histories
            query = select(Medicalhistory).where(
                Medicalhistory.patient_mrn == patient_mrn
            ).order_by(desc(Medicalhistory.medicalhistory_date)).limit(limit)
            
            result = await db.execute(query)
            histories = result.scalars().all()
            
            # Format medical histories with reference IDs and apply tag filter if needed
            formatted_histories = []
            for history in histories:
                # Apply tag filter if specified
                if tag_filter and history.tags:
                    if not any(tag_filter.lower() in tag.lower() for tag in history.tags):
                        continue
                
                reference_id = f"medicalhistories_{history.medicalhistory_id}"
                formatted_histories.append({
                    "reference_id": reference_id,
                    "title": history.medicalhistory_title,
                    "content": history.medicalhistory_content[:500] + "..." if len(history.medicalhistory_content) > 500 else history.medicalhistory_content,
                    "date": history.medicalhistory_date.isoformat(),
                    "tags": history.tags or [],
                    "doctor_id": history.doctor_id
                })
            
            return {
                "record_type": "medical_histories",
                "patient_mrn": patient_mrn,
                "filter_applied": tag_filter,
                "medical_histories": formatted_histories,
                "count": len(formatted_histories),
                "reference_instruction": "Use reference_id in square brackets to cite these medical histories, e.g., [medicalhistories_ghi789]"
            }
        except Exception as e:
            return {"error": f"Failed to retrieve medical histories: {str(e)}"}
    
    @tool(description="Get recent examinations for the patient. Use this to find imaging studies, diagnostic tests, physical examinations, and clinical assessments.")
    async def get_recent_examinations_with_context(
        limit: int = Field(default=5, description="Maximum number of recent examinations to return (default 5)")
    ) -> Dict[str, Any]:
        if not db:
            return {"error": "Database connection not available"}
        
        try:
            from app.core.db.schema import Examination
            from sqlalchemy import select, desc
            
            # Build query for patient's examinations
            query = select(Examination).where(
                Examination.patient_mrn == patient_mrn
            ).order_by(desc(Examination.examination_date)).limit(limit)
            
            result = await db.execute(query)
            examinations = result.scalars().all()
            
            # Format examinations with reference IDs
            formatted_examinations = []
            for examination in examinations:
                reference_id = f"examinations_{examination.examination_id}"
                formatted_examinations.append({
                    "reference_id": reference_id,
                    "title": examination.examination_title,
                    "examination_date": examination.examination_date.isoformat(),
                    "doctor_id": examination.doctor_id
                })
            
            return {
                "record_type": "examinations",
                "patient_mrn": patient_mrn,
                "examinations": formatted_examinations,
                "count": len(formatted_examinations),
                "reference_instruction": "Use reference_id in square brackets to cite these examinations, e.g., [examinations_jkl012]"
            }
        except Exception as e:
            return {"error": f"Failed to retrieve examinations: {str(e)}"}
    
    @tool(description="Get recent lab results for the patient. Use this to find blood tests, lab values, diagnostic markers, and test results with normal ranges.")
    async def get_recent_lab_results_with_context(
        limit: int = Field(default=10, description="Maximum number of recent lab results to return (default 10)"),
        test_name_filter: Optional[str] = Field(default=None, description="Filter by test name (e.g., 'glucose', 'hemoglobin', 'cholesterol')")
    ) -> Dict[str, Any]:
        if not db:
            return {"error": "Database connection not available"}
        
        try:
            from app.core.db.schema import LabResult
            from sqlalchemy import select, desc
            
            # Build query for patient's lab results
            query = select(LabResult).where(
                LabResult.patient_mrn == patient_mrn
            ).order_by(desc(LabResult.lab_date)).limit(limit)
            
            # Add test name filter if specified
            if test_name_filter:
                query = query.where(LabResult.test_name.ilike(f"%{test_name_filter}%"))
            
            result = await db.execute(query)
            lab_results = result.scalars().all()
            
            # Format lab results with reference IDs
            formatted_results = []
            for lab_result in lab_results:
                reference_id = f"labresults_{lab_result.lab_result_id}"
                formatted_results.append({
                    "reference_id": reference_id,
                    "test_name": lab_result.test_name,
                    "result_value": lab_result.result_value,
                    "normal_values": lab_result.normal_values,
                    "unit": lab_result.unit,
                    "lab_date": lab_result.lab_date.isoformat(),
                    "medicalhistory_id": lab_result.medicalhistory_id
                })
            
            return {
                "record_type": "lab_results",
                "patient_mrn": patient_mrn,
                "filter_applied": test_name_filter,
                "lab_results": formatted_results,
                "count": len(formatted_results),
                "reference_instruction": "Use reference_id in square brackets to cite these lab results, e.g., [labresults_123]"
            }
        except Exception as e:
            return {"error": f"Failed to retrieve lab results: {str(e)}"}
    
    # Only include patient-specific tools if patient_mrn is provided
    tools = [
        web_search,  # No context needed - general medical information search
        get_general_info_with_context,
    ]
    
    # Add patient-specific tools only when patient context is available
    if patient_mrn:
        tools.extend([
            get_recent_notes_with_context,
            get_recent_appointments_with_context,
            get_recent_medical_histories_with_context,
            get_recent_examinations_with_context,
            get_recent_lab_results_with_context,
        ])
    
    return tools