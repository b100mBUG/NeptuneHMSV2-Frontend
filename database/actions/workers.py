from database.models import Worker
from config_db import async_session
from sqlalchemy import select
from database.utils import hash_pwd, is_verified_pwd

async def add_worker(hospital_id: int, worker_detail: dict):
    async with async_session.begin() as session:
        new_worker = Worker(
            hospital_id = hospital_id,
            worker_name = worker_detail.get("worker_name", None),
            worker_email = worker_detail.get("worker_email", None),
            worker_phone = worker_detail.get("worker_phone", None),
            worker_role = worker_detail.get("worker_role", None),
            worker_password = hash_pwd(worker_detail.get("worker_password", "@worker_test") or "@worker_test")
        )
        try:
            session.add(new_worker)
            return new_worker
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_workers(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = select(Worker).where(Worker.hospital_id == hospital_id)
        if sort_term == "name":
            if sort_dir == "asc":
                stmt = stmt.order_by(Worker.worker_name.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Worker.worker_name.desc())
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(Worker.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Worker.date_added.desc())
        result = await session.execute(stmt)
        workers = result.scalars().all()
        if not workers:
            return None
        return workers

async def search_workers(hospital_id: int, search_by: str, search_term: str):
    async with async_session.begin() as session:
        stmt = select(Worker).where(Worker.hospital_id == hospital_id)
        if search_by == "name":
            stmt = stmt.where(Worker.worker_name.ilike(f"%{search_term}%"))
        elif search_by == "email":
            stmt = stmt.where(Worker.worker_email.ilike(f"%{search_term}%"))
        elif search_by == "phone":
            stmt = stmt.where(Worker.worker_phone.ilike(f"&{search_term}&"))
        result = await session.execute(stmt)
        workers = result.scalars().all()
        if not workers:
            return None
        return workers

async def get_specific_worker(hospital_id: int, worker_id: int):
    async with async_session.begin() as session:
        stmt = select(Worker).where(
            (Worker.hospital_id == hospital_id) &
            (Worker.worker_id == worker_id)
        )
        result = await session.execute(stmt)
        worker = result.scalars().first()
        if not worker:
            return None
        return worker

async def signin(hospital_id: int, worker_detail):
    async with async_session.begin() as session:
        stmt = select(Worker).where(
            (Worker.hospital_id == hospital_id) &
            (Worker.worker_email == worker_detail.get("worker_email"))
        )
        result = await session.execute(stmt)
        worker = result.scalars().first()
        if not worker:
            return None
        if not is_verified_pwd(worker_detail.get("worker_password"), worker.worker_password):
            return None
        return worker

async def edit_workers(hospital_id: int, worker_id: int, worker_detail: dict):
    async with async_session.begin() as session:
        stmt = select(Worker).where(
            (Worker.hospital_id == hospital_id)&
            (Worker.worker_id == worker_id)
        )
        result = await session.execute(stmt)
        worker = result.scalars().first()
        if not worker:
            return None
        try:
            worker.worker_name = worker_detail.get("worker_name", None)
            worker.worker_email = worker_detail.get("worker_email", None)
            worker.worker_phone = worker_detail.get("worker_phone", None)
            worker.worker_role = worker_detail.get("worker_role", None)

            return worker
        except Exception as e:
            print("An error occurred: ", e)

async def change_password(hospital_id, worker_id, password_detail):
    async with async_session.begin() as session:
        stmt = select(Worker).where(
            (Worker.hospital_id == hospital_id)&
            (Worker.worker_id == worker_id)
        )
        result = await session.execute(stmt)
        worker = result.scalars().first()
        if not worker:
            print("Worker not found")
            return None
        
        if not is_verified_pwd(password_detail.get("former_password"), worker.worker_password):
            print("Unable to authenticate")
            return None
        try:
            worker.worker_password = hash_pwd(password_detail.get("new_password", "@worker_test"))
        except Exception as e:
            print("An error occurred: ", e)
        return worker

async def delete_worker(hospital_id: int, worker_id: int):
    async with async_session.begin() as session:
        stmt = select(Worker).where(
            (Worker.hospital_id == hospital_id) &
            (Worker.worker_id == worker_id)
        )
        result = await session.execute(stmt)
        worker = result.scalars().first()
        if not worker:
            return None
        try:
            await session.delete(worker)
        except Exception as e:
            print("An error occurred: ", e)
            