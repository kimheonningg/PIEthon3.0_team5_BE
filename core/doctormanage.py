from datetime import datetime

# from core.models.doctor import Doctor
from core.db import admin_db

# NOT IN USE
# async def create_new_doctor(doctorInfo: Doctor):
#     try:
#         doc = doctorInfo.model_dump(by_alias=True) 
#         doc["createdAt"] = datetime.utcnow()
#         result = await admin_db.doctors.insert_one(doc)
#         return {"success": True}
#     except:
#         return {"success": False}
