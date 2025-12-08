from datetime import datetime, date, timedelta
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated = "auto")


def hash_pwd(password):
    return pwd_context.hash(password)

def is_verified_pwd(hashed_pwd, inputted_pwd):
    return pwd_context.verify(hashed_pwd, inputted_pwd)

def current_date():
    today = datetime.today().date()
    return today

def convert_to_date(date_str: str):
    to_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    return to_date

def date_to_str(date_obj: datetime):
    to_str = datetime.strftime(date_obj, "%Y-%m-%d")
    return to_str

def expiry_date():
    today = datetime.now()
    expiry = today + timedelta(minutes=2)
    return expiry
