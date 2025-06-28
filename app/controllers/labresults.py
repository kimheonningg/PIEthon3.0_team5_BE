from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from app.service.postgres.labresultmanage import (
    create_new_lab_result,
    get_lab_results_by_patient
)
from app.service.postgres.medicalhistorymanage import create_new_medicalhistory
from app.service.parsing.upstage_parser import UpstageParser
from app.dto.labresult import LabResult as LabResultModel
from app.dto.medicalhistory import Medicalhistory as MedicalhistoryModel
from app.core.auth import get_current_user
from app.core.db import get_db, User

router = APIRouter()

@router.post("/parse_and_create")
async def parse_lab_image_and_create(
    patient_mrn: str = Form(...),
    lab_date: str = Form(...),  # ISO format string
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    이미지를 파싱하여 Lab Results를 생성합니다.
    1. Medicalhistory 생성 (title: "Lab History", content: 전체 JSON)
    2. 각 테스트 결과를 LabResult로 저장
    """
    try:
        # 이미지 파일 읽기
        image_bytes = await image.read()
        
        # UpstageParser로 이미지 파싱
        parser = UpstageParser()
        parsed_data = parser.extract(image_bytes)
        
        # lab_date 문자열을 datetime으로 변환
        lab_datetime = datetime.fromisoformat(lab_date.replace('Z', '+00:00'))
        
        # 1. Medicalhistory 생성
        medicalhistory_info = MedicalhistoryModel(
            medicalhistory_title="Lab History",
            medicalhistory_content=json.dumps(parsed_data, ensure_ascii=False, indent=2),
            medicalhistory_date=lab_datetime,
            patient_mrn=patient_mrn,
            tags=["lab", "parsed"]
        )
        
        medicalhistory_result = await create_new_medicalhistory(
            medicalhistory_info, db, current_user
        )
        
        if not medicalhistory_result.get("success"):
            raise HTTPException(status_code=500, detail="Failed to create medical history")
        
        # medicalhistory_id 가져오기
        medicalhistory_id = medicalhistory_result.get("medicalhistory_id")
        
        # 2. 각 테스트 결과를 LabResult로 저장
        created_lab_results = []
        
        # parsed_data에서 tests 배열 확인
        tests = parsed_data.get("tests", [])
        if not tests:
            raise HTTPException(status_code=400, detail="No test results found in parsed data")
        
        for test in tests:
            lab_result_info = LabResultModel(
                test_name=test.get("testName", ""),
                normal_values=test.get("normalValues", ""),
                unit=test.get("unit", ""),
                lab_date=lab_datetime,
                medicalhistory_id=medicalhistory_id,
                patient_mrn=patient_mrn
            )
            
            result = await create_new_lab_result(lab_result_info, db, current_user)
            if result.get("success"):
                created_lab_results.append({
                    "test_name": test.get("testName"),
                    "normal_values": test.get("normalValues"),
                    "unit": test.get("unit")
                })
        
        return {
            "success": True,
            "message": f"Successfully created {len(created_lab_results)} lab results",
            "medicalhistory_id": medicalhistory_id,
            "lab_results_count": len(created_lab_results),
            "parsed_title": parsed_data.get("title", ""),
            "created_lab_results": created_lab_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing lab image: {str(e)}")

@router.get("/{patient_mrn}")
async def get_patient_lab_results(
    patient_mrn: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """특정 환자의 모든 Lab Results 조회"""
    result = await get_lab_results_by_patient(patient_mrn, db)
    return result 