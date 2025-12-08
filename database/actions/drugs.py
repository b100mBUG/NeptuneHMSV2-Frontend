from database.models import Drug, Billing
from config_db import async_session
from sqlalchemy import select
from datetime import datetime
async def add_drugs(hospital_id: int, drug_detail: dict):
    async with async_session.begin() as session:
        new_drug = Drug(
            hospital_id = hospital_id,
            drug_name = drug_detail.get("drug_name", None),
            drug_category = drug_detail.get("drug_category", None),
            drug_desc = drug_detail.get("drug_desc", None),
            drug_quantity = drug_detail.get("drug_quantity", 0),
            drug_price = drug_detail.get("drug_price", 0),
            drug_expiry = drug_detail.get("drug_expiry", None)
        )
        try:
            session.add(new_drug)
            return new_drug
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_drugs(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = select(Drug).where(Drug.hospital_id == hospital_id)
        if sort_term == "name":
            if sort_dir == "asc":
                stmt = stmt.order_by(Drug.drug_name.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Drug.drug_name.desc())
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(Drug.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Drug.date_added.desc())
        result = await session.execute(stmt)
        drugs = result.scalars().all()
        if not drugs:
            return None
        return drugs

async def search_drugs(hospital_id: int, search_term: str):
    async with async_session.begin() as session:
        stmt = select(Drug).where(Drug.hospital_id == hospital_id).where(Drug.drug_name.ilike(f"%{search_term}%"))
        result = await session.execute(stmt)
        drugs = result.scalars().all()
        if not drugs:
            return None
        return drugs

async def sale_drug(hospital_id: int, drug_id: int, drug_qty: int):
    async with async_session() as session:
        stmt = select(Drug).where(
            (Drug.hospital_id == hospital_id) &
            (Drug.drug_id == drug_id)
        )
        result = await session.execute(stmt)
        drug = result.scalars().first()

        if not drug:
            print("Drug not found")
            return {"status": "error", "message": "Drug not found"}
        if drug.drug_quantity < drug_qty:
            print("Insufficient stock")
            return {"status": "error", "message": "Insufficient stock"}
        if drug.drug_expiry < datetime.now():
            print("Drug expired")
            return {"status": "error", "message": "Drug expired"}

        try:
            total_price = drug.drug_price * drug_qty
            drug.drug_quantity -= drug_qty

            billing = Billing(
                hospital_id=hospital_id,
                source="POS",
                item=drug.drug_name,
                total=total_price,
            )
            session.add(billing)
            await session.commit()

            print("Sale successful")
            return {"status": "success"}

        except Exception as e:
            await session.rollback()
            print("Error during sale:", e)
            return {"status": "error", "message": str(e)}

async def get_specific_drug(hospital_id: int, drug_id: int):
    async with async_session.begin() as session:
        stmt = select(Drug).where(
            (Drug.hospital_id == hospital_id) &
            (Drug.drug_id == drug_id)
        )
        result = await session.execute(stmt)
        drug = result.scalars().first()
        if not drug:
            return None
        return drug

async def edit_drug(hospital_id: int, drug_id: int, drug_detail: dict):
    async with async_session.begin() as session:
        stmt = select(Drug).where(
            (Drug.hospital_id == hospital_id)&
            (Drug.drug_id == drug_id)
        )
        result = await session.execute(stmt)
        drug = result.scalars().first()
        if not drug:
            return None
        try:
            drug.drug_name = drug_detail.get("drug_name", None)
            drug.drug_category = drug_detail.get("drug_category", None)
            drug.drug_desc = drug_detail.get("drug_desc", None)
            drug.drug_quantity = drug_detail.get("drug_quantity", 0)
            drug.drug_price = drug_detail.get("drug_price", 0)
            drug.drug_expiry = drug_detail.get("drug_expiry", None)
            return drug
        except Exception as e:
            print("An error occurred: ", e)
        
async def delete_drug(hospital_id: int, drug_id: int):
    async with async_session.begin() as session:
        drug = await get_specific_drug(hospital_id, drug_id)
        if not drug:
            return None
        drug = await session.merge(drug)
        try:
            await session.delete(drug)
        except Exception as e:
            print("An error occurred: ", e)
            