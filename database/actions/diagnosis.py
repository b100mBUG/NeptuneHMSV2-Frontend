from database.models import Diagnosis, Patient, Hospital, Billing
from config_db import async_session
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.utils import convert_to_date

async def add_diagnosis(hospital_id: int, diagnosis_detail: dict):
    async with async_session() as session:
        new_diagnosis = Diagnosis(
            hospital_id=hospital_id,
            patient_id=diagnosis_detail.get("patient_id"),
            diagnoser_id=diagnosis_detail.get("diagnoser_id"),
            symptoms=diagnosis_detail.get("symptoms"),
            findings=diagnosis_detail.get("findings"),
            suggested_diagnosis=diagnosis_detail.get("suggested_diagnosis"),
        )

        session.add(new_diagnosis)
        await session.commit()
        await session.flush()

        stmt = (
            select(Diagnosis)
            .options(selectinload(Diagnosis.patient))
            .where(Diagnosis.diagnosis_id == new_diagnosis.diagnosis_id)
        )
        result = await session.execute(stmt)
        diagnosis_with_patient = result.scalars().first()
        
        hosp_stmt = select(Hospital).where(
            Hospital.hospital_id == hospital_id
        )
        hosp_result = await session.execute(hosp_stmt)
        hospital = hosp_result.scalars().first()
        
        session.add(
            Billing(
                hospital_id = hospital_id,
                patient_id = diagnosis_detail.get("patient_id", None),
                source = "Diagnosis",
                item = "Diagnosis with doctor",
                total = hospital.diagnosis_fee,
            )
        )
        await session.commit()

        return diagnosis_with_patient

async def fetch_diagnosis(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = (
            select(Diagnosis)
            .where(Diagnosis.hospital_id == hospital_id)
            .options(selectinload(Diagnosis.patient))
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
                    .order_by(Patient.patient_name.desc())
                )
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(Diagnosis.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Diagnosis.date_added.desc())
        result = await session.execute(stmt)
        diagnoses = result.scalars().all()
        if not diagnoses:
            return None
        return diagnoses

async def search_diagnosis(hospital_id: int, search_term: str):
    async with async_session.begin() as session:
        stmt = (
            select(Diagnosis)
            .join(Patient)
            .where(
                (Diagnosis.hospital_id == hospital_id) &
                (Patient.patient_name.ilike(f"%{search_term}%"))
            )
            .options(selectinload(Diagnosis.patient))
        )
        result = await session.execute(stmt)
        diagnoses = result.scalars().all()
        if not diagnoses:
            return None
        return diagnoses

async def get_specific_diagnosis(hospital_id: int, diagnosis_id: int):
    async with async_session.begin() as session:
        stmt = (
            select(Diagnosis)
            .where(
                (Diagnosis.hospital_id == hospital_id) &
                (Diagnosis.diagnosis_id == diagnosis_id)
            )
            .options(selectinload(Diagnosis.patient))
        )
        result = await session.execute(stmt)
        diagnosis = result.scalars().first()
        if not diagnosis:
            return None
        return diagnosis

async def edit_diagnosis(hospital_id: int, diagnosis_id: int, diagnosis_detail: dict):
    async with async_session.begin() as session:
        diagnosis = await get_specific_diagnosis(hospital_id, diagnosis_id)
        if not diagnosis:
            return None
        diagnosis = await session.merge(diagnosis)
        try:
            diagnosis.symptoms = diagnosis_detail.get("symptoms", None)
            diagnosis.findings = diagnosis_detail.get("findings", None)
            diagnosis.suggested_diagnosis = diagnosis_detail.get("suggested_diagnosis", None)
            return diagnosis
        except Exception as e:
            print("An error occurred: ", e)
        
async def delete_diagnosis(hospital_id: int, diagnosis_id: int):
    async with async_session.begin() as session:
        diagnosis = await get_specific_diagnosis(hospital_id, diagnosis_id)
        if not diagnosis:
            return None
        diagnosis = await session.merge(diagnosis)
        try:
            await session.delete(diagnosis)
        except Exception as e:
            print("An error occurred: ", e)
            