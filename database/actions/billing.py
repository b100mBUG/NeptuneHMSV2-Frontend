from database.models import Billing
from config_db import async_session
from sqlalchemy import select
from datetime import datetime

async def show_total_billings(hospital_id: int):
    async with async_session() as session:
        stmt = select(Billing).where(
            Billing.hospital_id == hospital_id
        )
        result = await session.execute(stmt)
        billings = result.scalars().all()
        if not billings:
            return None
        return billings

async def show_total_patient_billings(hospital_id: int, patient_id: int):
    async with async_session() as session:
        stmt = select(Billing).where(
            (Billing.hospital_id == hospital_id) &
            (Billing.patient_id == patient_id)
        )
        result = await session.execute(stmt)
        billings = result.scalars().all()
        if not billings:
            return None
        return billings

async def show_total_patient_billings_today(hospital_id: int, patient_id: int):
    async with async_session() as session:
        stmt = select(Billing).where(
            (Billing.hospital_id == hospital_id) &
            (Billing.patient_id == patient_id) &
            (Billing.created_at == datetime.today())
        )
        result = await session.execute(stmt)
        billings = result.scalars().all()
        if not billings:
            return None
        return billings