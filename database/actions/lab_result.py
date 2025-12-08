from database.models import LaboratoryResult, Patient
from config_db import async_session
from sqlalchemy import select
from database.utils import convert_to_date
from sqlalchemy.orm import selectinload

async def add_lab_result(hospital_id: int, result_detail: dict):
    async with async_session() as session:
        new_result = LaboratoryResult(
            hospital_id = hospital_id,
            patient_id = result_detail.get("patient_id", None),
            tech_id = result_detail.get("tech_id", None),
            observations = result_detail.get("observations", None),
            conclusion = result_detail.get("conclusion", None),
        )
        try:
            session.add(new_result)
            await session.commit()
            await session.flush()
            stmt  = (
                select(LaboratoryResult).where(LaboratoryResult.result_id == new_result.result_id)
                .options(selectinload(LaboratoryResult.patient))
            )
            result = await session.execute(stmt)
            mega_new_result = result.scalars().first()
            return mega_new_result
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_lab_results(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = (
            select(LaboratoryResult).where(LaboratoryResult.hospital_id == hospital_id)
            .options(selectinload(LaboratoryResult.patient))
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
                stmt = stmt.order_by(LaboratoryResult.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(LaboratoryResult.date_added.desc())
        result = await session.execute(stmt)
        lab_results = result.scalars().all()
        if not lab_results:
            return None
        return lab_results

async def search_lab_results(hospital_id: int, search_term: str):
    async with async_session.begin() as session:
        stmt = (
            select(LaboratoryResult)
            .join(Patient)
            .where(
                (LaboratoryResult.hospital_id == hospital_id) &
                (Patient.patient_name.ilike(f"%{search_term}%"))
            )
            .options(selectinload(LaboratoryResult.patient))
        )
        result = await session.execute(stmt)
        lab_results = result.scalars().all()
        if not lab_results:
            return None
        return lab_results

async def get_specific_result(hospital_id: int, result_id: int):
    async with async_session.begin() as session:
        stmt = (
            select(LaboratoryResult)
            .where(
                (LaboratoryResult.hospital_id == hospital_id) &
                (LaboratoryResult.result_id == result_id)
            )
            .options(selectinload(LaboratoryResult.patient))
        )
        result = await session.execute(stmt)
        lab_results = result.scalars().first()
        if not lab_results:
            return None
        return lab_results

async def edit_lab_result(hospital_id: int, result_id: int, result_detail: dict):
    async with async_session.begin() as session:
        result = await get_specific_result(hospital_id, result_id)
        if not result:
            return None
        result = await session.merge(result)
        try:
            result.observations = result_detail.get("observations", None)
            result.conclusion = result_detail.get("conclusion", None)
            return result
        except Exception as e:
            print("An error occurred: ", e)
        
async def delete_lab_result(hospital_id: int, result_id: int):
    async with async_session() as session:
        result = await session.get(LaboratoryResult, result_id)

        if not result or result.hospital_id != hospital_id:
            return None

        try:
            await session.delete(result)
            await session.commit()
            return {"status": "success"}
        except Exception as e:
            await session.rollback()
            print("An error occurred:", e)
            return {"status": "error", "detail": str(e)}
