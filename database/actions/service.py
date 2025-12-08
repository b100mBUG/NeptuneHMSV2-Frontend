from database.models import Service
from config_db import async_session
from sqlalchemy import select
from database.utils import convert_to_date

async def add_services(hospital_id: int, service_detail: dict):
    async with async_session.begin() as session:
        new_service = Service(
            hospital_id = hospital_id,
            service_name = service_detail.get("service_name", None),
            service_price = service_detail.get("service_price", 0),
            service_desc = service_detail.get("service_desc", None),
        )
        try:
            session.add(new_service)
            return new_service
        except Exception as e:
            print("An error occurred: ", e)

async def fetch_services(hospital_id: int, sort_term: str, sort_dir: str):
    async with async_session.begin() as session:
        stmt = select(Service).where(Service.hospital_id == hospital_id)
        if sort_term == "name":
            if sort_dir == "asc":
                stmt = stmt.order_by(Service.service_name.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Service.service_name.desc())
                
        elif sort_term == "date":
            if sort_dir == "asc":
                stmt = stmt.order_by(Service.date_added.asc())
            elif sort_dir == "desc":
                stmt = stmt.order_by(Service.date_added.desc())
        result = await session.execute(stmt)
        services = result.scalars().all()
        if not services:
            return None
        return services

async def search_services(hospital_id: int, search_term: str):
    async with async_session.begin() as session:
        stmt = select(Service).where(Service.hospital_id == hospital_id).where(Service.service_name.ilike(f"%{search_term}%"))
        result = await session.execute(stmt)
        services = result.scalars().all()
        if not services:
            return None
        return services

async def get_specific_service(hospital_id: int, service_id: int):
    async with async_session.begin() as session:
        stmt = select(Service).where(
            (Service.hospital_id == hospital_id) &
            (Service.service_id == service_id)
        )
        result = await session.execute(stmt)
        service = result.scalars().first()
        if not service:
            return None
        return service

async def edit_service(hospital_id: int, service_id: int, service_detail: dict):
    async with async_session.begin() as session:
        stmt = select(Service).where(
            (Service.hospital_id == hospital_id)&
            (Service.service_id == service_id)
        )
        result = await session.execute(stmt)
        service = result.scalars().first()
        if not service:
            return None
        try:
            service.service_name = service_detail.get("service_name", None)
            service.service_price = service_detail.get("service_price", 0)
            service.service_desc = service_detail.get("service_desc", None)
            return service
        except Exception as e:
            print("An error occurred: ", e)
        
async def delete_service(hospital_id: int, service_id: int):
    async with async_session.begin() as session:
        service = await get_specific_service(hospital_id, service_id)
        if not service:
            return None
        service = await session.merge(service)
        try:
            await session.delete(service)
        except Exception as e:
            print("An error occurred: ", e)
            