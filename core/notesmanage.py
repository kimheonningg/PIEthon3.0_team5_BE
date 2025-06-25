# file for functions that handle medical notes
from datetime import datetime
from typing import Dict, Any
from bson import ObjectId
from fastapi import HTTPException, status

from core.models.noteform import CreateNoteForm, UpdateNoteForm
from core.db import admin_db, data_db

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
        "doctorId": [str(doctorInfo.get("_id"))],
        "patientId": patientId,
        "createdAt": now,
        "lastModified": now,
        "title": noteIn.title,
        "content": noteIn.content,
        "noteType": noteIn.noteType,
        "deleted": False,
    }

    insert_result = await data_db.notes.insert_one(noteDoc)

    if not insert_result.acknowledged:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="저장에 실패했습니다."
        )

    update_result = await admin_db.patients.update_one(
        {"patientId": patientId},
        {"$push": {
            "doctorId": str(doctorInfo["_id"]),
            "medicalNotes": noteOid
        }},
    )

    if update_result.modified_count == 0:
        await data_db.notes.delete_one({"_id": noteOid})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="노트는 생성되었으나 환자 문서 업데이트에 오류가 발생했습니다."
        )

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
        set_ops["title"] = noteIn.title
    if noteIn.content is not None:
        set_ops["content"] = noteIn.content
    if noteIn.noteType is not None:
        set_ops["noteType"] = noteIn.noteType

    if not set_ops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 내용이 없습니다.",
        )

    set_ops["lastModified"] = datetime.utcnow()

    update_doc: Dict[str, Any] = {
        "$set": set_ops, 
        "$push": {"doctorId": str(doctorInfo.get("_id"))},
    }

    update_result = await data_db.notes.update_one(
        {"_id": str(noteId), "deleted": False},
        update_doc,
    )

    updated_note = await data_db.notes.find_one({"_id": str(noteId)})

    return {"success": True, "note": updated_note}

async def get_all_notes(
    patientId: str,
    doctorInfo: Dict,
):
    if doctorInfo["position"] != "doctor":
        raise HTTPException(403, "의사만 노트를 조회할 수 있습니다.")

    patient_exists = await admin_db.patients.find_one(
        {"patientId": patientId}, {"_id": 1}
    )
    if not patient_exists:
        raise HTTPException(404, "환자 정보가 없습니다.")
    
    cursor = data_db.notes.find(
        {"patientId": patientId, "deleted": False}
    ).sort("lastModified", -1)

    notes = await cursor.to_list(length=None)

    return {"success": True, "notes": notes}

async def get_specific_note(
    noteId: str,
    doctorInfo: Dict,
):
    if doctorInfo.get("position") != "doctor":
        raise HTTPException(403, "의사만 노트를 조회할 수 있습니다.")
    
    note = await data_db.notes.find_one(
        {"_id": str(noteId), "deleted": False}
    )

    if not note:
        raise HTTPException(404, "노트를 찾을 수 없습니다.")

    return {"success": True, "note": note}