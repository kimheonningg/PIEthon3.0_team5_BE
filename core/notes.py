# file for functions that handle medical notes
from datetime import datetime
from typing import Dict
from bson import ObjectId
from fastapi import HTTPException, status

from core.models.createnoteform import CreateNoteForm
from core.db import admin_db

async def add_new_note(
    patientId: str,
    noteIn: CreateNoteForm,
    doctorInfo: Dict,
) -> Dict:
    if doctorInfo["position"] != "doctor":
        raise HTTPException(403, "Only doctors can create medical notes.")
        
    patient = await admin_db.users.find_one(
        {"patientId": patientId, "position": "patient"},
        projection={"_id": 1},
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    now = datetime.utcnow()
    noteDoc = {
        "doctorId": str(doctorInfo["_id"]),
        "patientId": patientId,
        "createdAt": now,
        "lastModified": now,
        "title": noteIn.title,
        "content": noteIn.content,
        "noteType": noteIn.noteType,
        "deleted": False,
    }

    result = await admin_db.users.update_one(
        {"patientId": patientId}, {"$push": {"medicalNotes": noteDoc}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    success = result.modified_count == 1
    if not success:
        raise HTTPException(status_code=500, detail="Failed to append medical note")

    return {"success": True, "note": noteDoc}