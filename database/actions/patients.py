from database.models import Patient
from config_db import async_session
from sqlalchemy import select

async def add_patients(hospital_id: int, patient_detail: dict):
    async with async_session.begin() as session:
        new_patient = Patient(
            hospital_id = hospital_id,
            patient_name = patient_detail.get("patient_name", None),
            patient_email = patient_detail.get("patient_email", None),
            patient_phone = patient_detail.get("patient_phone", None),
            patient_id_number = patient_detail.get("patient_id_number", None),
            patient_gender = patient_detail.get("patient_gender", None),
            patient_address = patient_detail.get("patient_address", None),
            patient_dob = patient_detail.get("patient_dob", None),
            patient_weight = patient_detail.get("patient_weight", 0),
            patient_chronic_condition = patient_detail.get("chronic_condition", None),
            patient_allergy  = patient_detail.get("patient_allergy", None),
            patient_avg_pulse = patient_detail.get("patient_avg_pulse", 0),
            patient_bp = patient_detail.get("patient_bp", 0),
            patient_blood_type = patient_detail.get("patient_blood_type", None)
        )
        try:
            session.add(new_patient)
            return new_patient
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_patients(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = select(Patient).where(Patient.hospital_id == hospital_id)
        if sort_term == "name":
            if sort_dir == "asc":
                stmt = stmt.order_by(Patient.patient_name.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Patient.patient_name.desc())
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(Patient.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Patient.date_added.desc())
        result = await session.execute(stmt)
        patients = result.scalars().all()
        if not patients:
            return None
        return patients

async def search_patients(hospital_id: int, search_by: str, search_term: str):
    async with async_session.begin() as session:
        stmt = select(Patient).where(Patient.hospital_id == hospital_id)
        if search_by == "name":
            stmt = stmt.where(Patient.patient_name.ilike(f"%{search_term}%"))
        elif search_by == "email":
            stmt = stmt.where(Patient.patient_email.ilike(f"%{search_term}%"))
        elif search_by == "phone":
            stmt = stmt.where(Patient.patient_phone.ilike(f"%{search_term}%"))
        if search_by == "id_number":
            stmt = stmt.where(Patient.patient_id_number.ilike(f"%{search_term}%"))
        result = await session.execute(stmt)
        patients = result.scalars().all()
        if not patients:
            return None
        return patients

async def get_specific_patient(hospital_id: int, patient_id: int):
    async with async_session.begin() as session:
        stmt = select(Patient).where(
            (Patient.hospital_id == hospital_id) &
            (Patient.patient_id == patient_id)
        )
        result = await session.execute(stmt)
        patient = result.scalars().first()
        if not patient:
            return None
        return patient

async def edit_patients(hospital_id: int, patient_id: int, patient_detail: dict):
    async with async_session.begin() as session:
        stmt = select(Patient).where(
            (Patient.hospital_id == hospital_id)&
            (Patient.patient_id == patient_id)
        )
        result = await session.execute(stmt)
        patient = result.scalars().first()
        if not patient:
            return None
        patient = await session.merge(patient)
        try:
            patient.patient_name = patient_detail.get("patient_name", None)
            patient.patient_email = patient_detail.get("patient_email", None)
            patient.patient_phone = patient_detail.get("patient_phone", None)
            patient.patient_id_number = patient_detail.get("patient_id_number", None)
            patient.patient_gender = patient_detail.get("patient_gender", None)
            patient.patient_address = patient_detail.get("patient_address", None)
            patient.patient_dob = patient_detail.get("patient_dob", None)
            patient.patient_weight = patient_detail.get("patient_weight", 0)
            patient.patient_avg_pulse = patient_detail.get("patient_avg_pulse", 0)
            patient.patient_bp = patient_detail.get("patient_bp", 0)
            patient.patient_chronic_condition = patient_detail.get("patient_chronic_condition", None)
            patient.patient_allergy = patient_detail.get("patient_allergy", None)
            patient.patient_blood_type = patient_detail.get("patient_blood_type", None)
            return patient
        except Exception as e:
            print("An error occurred: ", e)
        
async def delete_patient(hospital_id: int, patient_id: int):
    async with async_session.begin() as session:
        stmt = select(Patient).where(
            (Patient.hospital_id == hospital_id) &
            (Patient.patient_id == patient_id)
        )
        result = await session.execute(stmt)
        patient = result.scalars().first()
        if not patient:
            return None
        patient = await session.merge(patient)
        try:
            await session.delete(patient)
        except Exception as e:
            print("An error occurred: ", e)
            