from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import User, Patient, LabResult
from app.dto.labresult import LabResult as LabResultModel

async def create_new_lab_result(
    lab_result_info: LabResultModel,
    db: AsyncSession,
    doctor_info: User
):
    try:
        lab_result = LabResult(
            test_name=lab_result_info.test_name,
            result_value=lab_result_info.result_value,
            normal_values=lab_result_info.normal_values,
            unit=lab_result_info.unit,
            lab_date=lab_result_info.lab_date,
            medicalhistory_id=lab_result_info.medicalhistory_id,
            patient_mrn=lab_result_info.patient_mrn
        )
        db.add(lab_result)
        await db.commit()
        return {"success": True}
    except Exception as e:
        await db.rollback()
        print(f"[create_new_lab_result error] {e}")
        return {"success": False, "error": str(e)}

async def get_lab_results_by_patient(
    patient_mrn: str,
    db: AsyncSession
):
    try:
        result = await db.execute(
            select(LabResult).where(LabResult.patient_mrn == patient_mrn)
        )
        lab_results = result.scalars().all()
        serialized = [
            {
                "lab_result_id": lr.lab_result_id,
                "test_name": lr.test_name,
                "result_value": lr.result_value,
                "normal_values": lr.normal_values,
                "unit": lr.unit,
                "lab_date": lr.lab_date,
                "medicalhistory_id": lr.medicalhistory_id,
                "patient_mrn": lr.patient_mrn
            }
            for lr in lab_results
        ]
        return {"success": True, "lab_results": serialized}
    except Exception as e:
        print(f"[get_lab_results_by_patient error] {e}")
        return {"success": False, "error": str(e)}
