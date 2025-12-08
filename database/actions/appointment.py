from database.models import Appointment, Patient, Billing, Service
from config_db import async_session
from sqlalchemy import select
from datetime import datetime
from sqlalchemy.orm import selectinload

async def add_appointment(hospital_id: int, appointment_detail: dict):
    async with async_session() as session:
        print("Appointment detail before entering DB: ", appointment_detail)
        new_appointment = Appointment(
            hospital_id = hospital_id,
            patient_id = appointment_detail.get("patient_id", None),
            consultant_id = appointment_detail.get("consultant_id", None),
            service_id = appointment_detail.get("service_id", None),
            appointment_desc = appointment_detail.get("appointment_desc", None),
            date_requested = appointment_detail.get("date_scheduled", None),
            time_requested = appointment_detail.get("time_scheduled", None)
        )
        try:
            session.add(new_appointment)
            await session.commit()
            await session.flush()
            stmt = (
                select(Appointment)
                .where(Appointment.appointment_id == new_appointment.appointment_id)
                .options(selectinload(Appointment.patient))
                .options(selectinload(Appointment.service))
                .options(selectinload(Appointment.consultant))
            )
            result = await session.execute(stmt)
            mega_new_appointment = result.scalars().first()
            serv_stmt = select(Service).where(
                Service.service_id == new_appointment.service_id
            )
            serv_result = await session.execute(serv_stmt)
            service = serv_result.scalars().first()
            session.add(
                Billing(
                    hospital_id = hospital_id,
                    patient_id = appointment_detail.get("patient_id", None),
                    source = "Appointments",
                    item = service.service_name,
                    total = service.service_price,
                )
            )
            await session.commit()
            return mega_new_appointment
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_appointments(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = (
            select(Appointment).where(Appointment.hospital_id == hospital_id)
            .options(selectinload(Appointment.patient))
            .options(selectinload(Appointment.service))
            .options(selectinload(Appointment.consultant))
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
                stmt = stmt.order_by(Appointment.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Appointment.date_added.desc())
        result = await session.execute(stmt)
        appointments = result.scalars().all()
        if not appointments:
            return None
        return appointments

async def search_appointments(hospital_id: int, search_term: str):
    async with async_session.begin() as session:
        stmt = (
            select(Appointment)
            .join(Patient)
            .where(
                (Appointment.hospital_id == hospital_id) &
                (Patient.patient_name.ilike(f"%{search_term}%"))
            )
            .options(selectinload(Appointment.patient))
            .options(selectinload(Appointment.service))
            .options(selectinload(Appointment.consultant))
        )
        result = await session.execute(stmt)
        appointments = result.scalars().all()
        if not appointments:
            return None
        return appointments

async def get_specific_appointment(hospital_id: int, appointment_id: int):
    async with async_session.begin() as session:
        stmt = (
            select(Appointment)
            .where(
                (Appointment.hospital_id == hospital_id) &
                (Appointment.appointment_id == appointment_id)
            )
            .options(selectinload(Appointment.patient))
            .options(selectinload(Appointment.service))
            .options(selectinload(Appointment.consultant))
        )
        result = await session.execute(stmt)
        appointment = result.scalars().first()
        if not appointment:
            return None
        return appointment

async def edit_appointment(hospital_id: int, appointment_id: int, appointment_detail: dict):
    async with async_session.begin() as session:
        print("Data before editing: ", appointment_detail)
        appointment = await get_specific_appointment(hospital_id, appointment_id)
        if not appointment:
            return None
        appointment = await session.merge(appointment)
        try:
            appointment.appointment_desc = appointment_detail.get("appointment_desc", None)
            appointment.date_requested = appointment_detail.get("date_scheduled", None)
            appointment.time_requested = appointment_detail.get("time_scheduled", None)
            return appointment
        except Exception as e:
            print("An error occurred: ", e)
        
async def delete_appointment(hospital_id: int, appointment_id: int):
    async with async_session.begin() as session:
        appointment = await get_specific_appointment(hospital_id, appointment_id)
        if not appointment:
            return None
        appointment = await session.merge(appointment)
        try:
            await session.delete(appointment)
        except Exception as e:
            print("An error occurred: ", e)