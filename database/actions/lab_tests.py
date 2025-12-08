from database.models import LaboratoryTest
from config_db import async_session
from sqlalchemy import select
from database.utils import convert_to_date

async def add_lab_tests(hospital_id: int, test_detail: dict):
    async with async_session.begin() as session:
        new_lab_test = LaboratoryTest(
            hospital_id = hospital_id,
            test_name = test_detail.get("test_name", None),
            test_price = test_detail.get("test_price", 0),
            test_desc = test_detail.get("test_desc", None),
        )
        try:
            session.add(new_lab_test)
            return new_lab_test
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_lab_tests(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = select(LaboratoryTest).where(LaboratoryTest.hospital_id == hospital_id)
        if sort_term == "name":
            if sort_dir == "asc":
                stmt = stmt.order_by(LaboratoryTest.test_name.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(LaboratoryTest.test_name.desc())
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(LaboratoryTest.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(LaboratoryTest.date_added.desc())
        result = await session.execute(stmt)
        tests = result.scalars().all()
        if not tests:
            return None
        return tests

async def search_lab_tests(hospital_id: int, search_term: str):
    async with async_session.begin() as session:
        stmt = select(LaboratoryTest).where(LaboratoryTest.hospital_id == hospital_id).where(LaboratoryTest.test_name.ilike(f"%{search_term}%"))
        result = await session.execute(stmt)
        tests = result.scalars().all()
        if not tests:
            return None
        return tests

async def get_specific_test(hospital_id: int, test_id: int):
    async with async_session.begin() as session:
        stmt = select(LaboratoryTest).where(
            (LaboratoryTest.hospital_id == hospital_id) &
            (LaboratoryTest.test_id == test_id)
        )
        result = await session.execute(stmt)
        test = result.scalars().first()
        if not test:
            return None
        return test

async def edit_lab_test(hospital_id: int, test_id: int, test_detail: dict):
    async with async_session.begin() as session:
        test = await get_specific_test(hospital_id, test_id)
        if not test:
            return None
        test = await session.merge(test)
        try:
            test.test_name = test_detail.get("test_name", None)
            test.test_price = test_detail.get("test_price", 0)
            test.test_desc = test_detail.get("test_desc", None)
            return test
        except Exception as e:
            print("An error occurred: ", e)
        
async def delete_lab_test(hospital_id: int, test_id: int):
    async with async_session.begin() as session:
        test = await get_specific_test(hospital_id, test_id)
        if not test:
            return None
        test = await session.merge(test)
        try:
            await session.delete(test)
        except Exception as e:
            print("An error occurred: ", e)
            