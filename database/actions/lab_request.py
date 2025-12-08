from database.models import LaboratoryRequest, Patient, Billing, LaboratoryTest
from config_db import async_session
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def add_lab_request(hospital_id: int, request_detail: dict):
    async with async_session() as session:
        new_request = LaboratoryRequest(
            hospital_id = hospital_id,
            patient_id = request_detail.get("patient_id", None),
            doctor_id = request_detail.get("doctor_id", None),
            test_id = request_detail.get("test_id", None),
        )
        try:
            session.add(new_request)
            await session.commit()
            await session.flush()
            stmt = (
                select(LaboratoryRequest)
                .where(LaboratoryRequest.request_id == new_request.request_id)
                .options(selectinload(LaboratoryRequest.patient))
                .options(selectinload(LaboratoryRequest.test))
            )
            result = await session.execute(stmt)
            mega_new_request = result.scalars().first()
            test_stmt = select(LaboratoryTest).where(
                LaboratoryTest.test_id == request_detail.get("test_id", 0)
            )
            test_result = await session.execute(test_stmt)
            test = test_result.scalars().first()
            
            session.add(
                Billing(
                    hospital_id = hospital_id,
                    patient_id = request_detail.get("patient_id", None),
                    source = "Lab Requests",
                    item = test.test_name,
                    total = test.test_price
                )
            )
            
            return mega_new_request
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_lab_requests(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = (
            select(LaboratoryRequest)
            .where(LaboratoryRequest.hospital_id == hospital_id)
            .options(selectinload(LaboratoryRequest.patient))
            .options(selectinload(LaboratoryRequest.test))
        )
        if sort_term == "name":
            if sort_dir == "asc":
                stmt = (
                    stmt
                    .join(Patient)
                    .order_by(Patient.patient_name.asc())
                )
            elif sort_dir == "desc":
                stmt = (
                    stmt
                    .join(Patient)
                    .order_by(Patient.patient_name.asc())
                )
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(LaboratoryRequest.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(LaboratoryRequest.date_added.desc())
        result = await session.execute(stmt)
        lab_requests = result.scalars().all()
        if not lab_requests:
            return None
        return lab_requests

async def search_lab_request(hospital_id: int, search_term: str):
    async with async_session.begin() as session:
        stmt = (
            select(LaboratoryRequest)
            .join(Patient)
            .where(
                (LaboratoryRequest.hospital_id == hospital_id) &
                (Patient.patient_name.ilike(f"%{search_term}%"))
            )
            .options(selectinload(LaboratoryRequest.patient))
            .options(selectinload(LaboratoryRequest.test))
        )
        result = await session.execute(stmt)
        lab_requests = result.scalars().all()
        if not lab_requests:
            return None
        return lab_requests

async def get_specific_lab_request(hospital_id: int, request_id: int):
    async with async_session.begin() as session:
        stmt = select(LaboratoryRequest).where(
            (LaboratoryRequest.hospital_id == hospital_id) &
            (LaboratoryRequest.request_id == request_id)
        )
        result = await session.execute(stmt)
        request = result.scalars().first()
        if not request:
            return None
        return request
        
async def delete_lab_request(hospital_id: int, request_id: int):
    async with async_session.begin() as session:
        request = await get_specific_lab_request(hospital_id, request_id)
        if not request:
            return None
        request = await session.merge(request)
        try:
            await session.delete(request)
            await session.commit()
        except Exception as e:
            print("An error occurred: ", e)
            