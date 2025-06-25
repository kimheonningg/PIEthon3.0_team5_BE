# file for functions that handle medical notes
from datetime import datetime
from typing import Dict
from bson import ObjectId
from fastapi import HTTPException, status

from core.models.noteform import CreateNoteForm, UpdateNoteForm
from core.db import admin_db

async def add_new_note(
    patientId: str,
    noteIn: CreateNoteForm,
    doctorInfo: Dict,
) -> Dict:
    if doctorInfo["position"] != "doctor":
        raise HTTPException(403, "의사만 환자 노트를 만들 수 있습니다.")
        
    patient = await admin_db.patients.find_one(
        {"patientId": patientId},
        projection={"_id": 1},
    )
    if not patient:
        raise HTTPException(status_code=404, detail="환자 정보가 없습니다. 환자 정보를 등록해주세요.")

    now = datetime.utcnow()
    noteOid = str(ObjectId())
    noteDoc = {
        "_id": noteOid,
        "doctorId": str(doctorInfo["_id"]),
        "patientId": patientId,
        "createdAt": now,
        "lastModified": now,
        "title": noteIn.title,
        "content": noteIn.content,
        "noteType": noteIn.noteType,
        "deleted": False,
    }

    result = await admin_db.patients.update_one(
        {"patientId": patientId}, {"$push": {"medicalNotes": noteDoc}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Patient not found")

    success = result.modified_count == 1
    if not success:
        raise HTTPException(status_code=500, detail="Failed to append medical note")

    return {"success": True, "note": noteDoc}

async def update_existing_note(
    noteId: str,
    noteIn: UpdateNoteForm,
    doctorInfo: Dict,
) -> Dict:
    if doctorInfo["position"] != "doctor":
        raise HTTPException(403, "의사만 수정할 수 있습니다.")
    
    patient = await admin_db.patients.find_one(
        {"patientId": noteIn.patientId},
        projection={"_id": 1},
    )

    if not patient:
        raise HTTPException(status_code=404, detail="환자 정보가 존재하지 않습니다.")

    set_ops: Dict[str, Any] = {}
    if noteIn.title is not None:
        set_ops["medicalNotes.$[note].title"] = noteIn.title
    if noteIn.content is not None:
        set_ops["medicalNotes.$[note].content"] = noteIn.content
    if noteIn.noteType is not None:
        set_ops["medicalNotes.$[note].noteType"] = noteIn.noteType
    set_ops["medicalNotes.$[note].lastModified"] = datetime.utcnow()

    if len(set_ops) == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 내용이 없습니다.",
        )
        
    note_id_filter = str(noteId)
    
    result = await admin_db.patients.update_one(
        {"patientId": noteIn.patientId},
        {"$set": set_ops},
        array_filters=[
            {
                "note._id": note_id_filter,
                "note.doctorId": str(doctorInfo["_id"]),
                "note.deleted": False,
            }
        ],
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you are not the author.",
        )

    return {"success": True}