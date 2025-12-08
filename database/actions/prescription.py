from database.models import Prescription, PrescriptionItem, Patient, Drug, Worker
from config_db import async_session
from sqlalchemy.orm import selectinload, joinedload
from database.models import Drug, Billing
from sqlalchemy import select
from datetime import datetime


async def add_prescription(hospital_id: int, prescription_detail: dict):
    async with async_session() as session:
        try:
            async with session.begin():
                new_presc_obj = Prescription(
                    hospital_id=hospital_id,
                    patient_id=prescription_detail.get("patient_id"),
                    prescriber_id=prescription_detail.get("prescriber_id"),
                )
                session.add(new_presc_obj)
                await session.flush()
                
                stmt = select(Drug).where(
                    Drug.drug_id == prescription_detail.get("drug_id")
                )
                res = await session.execute(stmt)
                drug = res.scalars().first()
                if not drug:
                    return None
                
                if drug.drug_quantity < prescription_detail.get("drug_qty", 0):
                    return None
                if drug.drug_expiry < datetime.today():
                    return None
                new_presc_item = PrescriptionItem(
                    prescription_id=new_presc_obj.prescription_id,
                    drug_id=prescription_detail.get("drug_id"),
                    drug_qty=prescription_detail.get("drug_qty", 0),
                    notes=prescription_detail.get("notes"),
                )
                try:
                    drug.drug_quantity -= prescription_detail.get("drug_qty", 0)
                    drug_qty = prescription_detail.get("drug_qty", 0)
                    total_price = drug.drug_price * drug_qty
                    
                    billing = Billing(
                        hospital_id=hospital_id,
                        patient_id = prescription_detail.get("patient_id", None),
                        source="Prescriptions",
                        item=drug.drug_name,
                        total=total_price,
                    )
                    session.add(billing)
                except Exception as e:
                    print("An error occurred during updating drug")
                session.add(new_presc_item)

            stmt = (
                select(Prescription)
                .where(Prescription.prescription_id == new_presc_obj.prescription_id)
                .options(
                    selectinload(Prescription.patient),
                    selectinload(Prescription.items).selectinload(PrescriptionItem.drug),
                    selectinload(Prescription.prescriber),
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

        except Exception as e:
            print("An error occurred:", e)
            await session.rollback()
            return None


async def fetch_prescriptions(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session() as session:
        stmt = (
            select(Prescription)
            .where(Prescription.hospital_id == hospital_id)
            .options(
                selectinload(Prescription.patient),
                selectinload(Prescription.items).selectinload(PrescriptionItem.drug),
                selectinload(Prescription.prescriber),
            )
        )

        if sort_term == "name":
            stmt = stmt.join(Patient)
            if sort_dir == "asc":
                stmt = stmt.order_by(Patient.patient_name.asc())
            else:
                stmt = stmt.order_by(Patient.patient_name.desc())
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(Prescription.date_added.asc())
            else:
                stmt = stmt.order_by(Prescription.date_added.desc())

        result = await session.execute(stmt)
        return result.scalars().unique().all() or None


async def search_prescriptions(hospital_id: int, search_term: str):
    async with async_session() as session:
        stmt = (
            select(Prescription)
            .join(Patient)
            .where(
                (Prescription.hospital_id == hospital_id)
                & (Patient.patient_name.ilike(f"%{search_term}%"))
            )
            .options(
                selectinload(Prescription.patient),
                selectinload(Prescription.items).selectinload(PrescriptionItem.drug),
                selectinload(Prescription.prescriber),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().unique().all() or None


async def get_specific_prescription(hospital_id: int, prescription_id: int):
    async with async_session() as session:
        stmt = (
            select(Prescription)
            .where(
                (Prescription.hospital_id == hospital_id)
                & (Prescription.prescription_id == prescription_id)
            )
            .options(
                selectinload(Prescription.patient),
                selectinload(Prescription.items).selectinload(PrescriptionItem.drug),
                selectinload(Prescription.prescriber),
            )
        )
        result = await session.execute(stmt)
        return result.scalars().first() or None


async def delete_prescription(hospital_id: int, prescription_id: int):
    async with async_session() as session:
        prescription = await session.get(Prescription, prescription_id)
        if not prescription:
            return None
        try:
            await session.delete(prescription)
            await session.commit()
        except Exception as e:
            print("An error occurred:", e)
