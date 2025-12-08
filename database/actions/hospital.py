from database.models import Hospital, Worker
from config_db import async_session
from sqlalchemy import select
import hashlib
from datetime import datetime
from database.utils import hash_pwd, is_verified_pwd

async def add_hospital(hospital_detail: dict):
    async with async_session.begin() as session:
        new_hospital = Hospital(
            hospital_name = hospital_detail.get("hospital_name", None),
            hospital_email = hospital_detail.get("hospital_email", None),
            hospital_contact = hospital_detail.get("hospital_contact", None),
            hospital_password = hash_pwd(hospital_detail.get("hospital_password", "@hospital_test")),
            diagnosis_fee = hospital_detail.get("diagnosis_fee", 0),
        )
        try:
            session.add(new_hospital)
            await session.flush()
            session.add(
                Worker(
                    hospital_id = new_hospital.hospital_id,
                    worker_name = "Admin",
                    worker_email = "admin_worker@gmail.com",
                    worker_phone = "0737841451",
                    worker_password = hash_pwd("admin"),
                    worker_role = "Admin"
                )
            )
            return new_hospital
        except Exception as e:
            print("An error occurred: ", e)
            
async def renew_hospital_plan(hospital_id: int, activation_key: str):
    async with async_session() as session:
        if not activation_key:
            return {"message": "Activation key empty!"}

        SECRET_KEY = "DROSOPHILLAMELANOGASTER"

        if "|" not in activation_key or len(activation_key.split("|")) != 3:
            return {"message": "Invalid key format. Expected 3 parts separated by '|'"}

        username, expiry_str, checksum = activation_key.split("|")
        expected_data = f"{username}-{expiry_str}-{SECRET_KEY}"
        expected_checksum = hashlib.sha256(expected_data.encode()).hexdigest()[:10].upper()

        if checksum != expected_checksum:
            return {"message": "Checksum mismatch"}

        expiry_time = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")

        if datetime.now() > expiry_time:
            return {"message": "Activation key expired!"}

        stmt = select(Hospital).where(Hospital.hospital_id == hospital_id)
        result = await session.execute(stmt)
        hospital = result.scalars().first()

        if not hospital:
            return {"message": "Hospital not found"}

        try:
            now = datetime.now()
            old_expiry = hospital.expiry_date

            extra_duration = expiry_time - now
            if old_expiry and old_expiry > now:
                remaining_duration = old_expiry - now
                new_expiry = now + remaining_duration + extra_duration
            else:
                new_expiry = now + extra_duration

            hospital.expiry_date = new_expiry
            await session.commit()

            return {"message": "renewed"}

        except Exception as e:
            return {"message": f"Error validating activation key: {e}"}

async def fetch_hospitals(sort_term: str, sort_dir: str):
    async with async_session() as session:
        stmt = select(Hospital)
        if sort_term == "name":
            if sort_dir == "asc":
                stmt = stmt.order_by(Hospital.hospital_name.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Hospital.hospital_name.desc())
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(Hospital.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Hospital.date_added.desc())
        result = await session.execute(stmt)
        hospitals = result.scalars().all()
        if not hospitals:
            return None
        return hospitals

async def search_hospitals(search_by: str, search_term: str):
    async with async_session() as session:
        stmt = select(Hospital)
        if search_by == "name":
            stmt = stmt.where(Hospital.hospital_name.ilike(f"%{search_term}%"))
        elif search_by == "email":
            stmt = stmt.where(Hospital.hospital_email.ilike(f"%{search_term}%"))
        elif search_by == "phone":
            stmt = stmt.where(Hospital.hospital_contact.ilike(f"%{search_term}%"))
        result = await session.execute(stmt)
        hospitals = result.scalars().all()
        if not hospitals:
            return None
        return hospitals

async def get_specific_hospital(hospital_id: int):
    async with async_session() as session:
        stmt = select(Hospital).where(
            Hospital.hospital_id == hospital_id
        )
        result = await session.execute(stmt)
        hospital = result.scalars().first()
        if not hospital:
            return None
        return hospital

async def signin(hospital_detail):
    async with async_session() as session:
        stmt = select(Hospital).where(
            (Hospital.hospital_email == hospital_detail.get("hospital_email"))
        )
        result = await session.execute(stmt)
        hospital = result.scalars().first()
        if not hospital:
            return None
        if not is_verified_pwd(hospital_detail.get("hospital_password"), hospital.hospital_password):
            return None
        return hospital

async def edit_hospital(hospital_id: int, hospital_detail: dict):
    async with async_session.begin() as session:
        hospital = await get_specific_hospital(hospital_id)
        if not hospital:
            return None
        hospital = await session.merge(hospital)
        try:
            hospital.hospital_name = hospital_detail.get("hospital_name", None)
            hospital.hospital_email = hospital_detail.get("hospital_email", None)
            hospital.hospital_contact = hospital_detail.get("hospital_contact", None)
            hospital.diagnosis_fee = hospital_detail.get("diagnosis_fee", 0)
            return hospital
        except Exception as e:
            print("An error occurred: ", e)

async def change_password(hospital_id, password_detail):
    async with async_session() as session:
        hospital = await get_specific_hospital(hospital_id)
        if not hospital:
            return None
        hospital = await session.merge(hospital)
        if not is_verified_pwd(password_detail.get("former_password"), hospital.hospital_password):
            return None
        try:
            hospital.hospital_password = hash_pwd(password_detail.get("new_password", "@hospital_test"))
            await session.commit()
            await session.refresh(hospital)
            return hospital
        except Exception as e:
            print("An error occurred: ", e)

async def delete_hospital(hospital_id: int):
    async with async_session.begin() as session:
        hospital = await get_specific_hospital(hospital_id)
        if not hospital:
            return None
        hospital = await session.merge(hospital)
        try:
            await session.delete(hospital)
        except Exception as e:
            print("An error occurred: ", e)
