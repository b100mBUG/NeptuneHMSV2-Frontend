from threading import Thread
from kivy.clock import mainthread

import requests
import asyncio

from config import SERVER_URL
from config import STORE
from utils import has_internet

store = STORE




def fetch_billings(filter, patient_id: int = 1, callback=None):
    Thread(target=start_online_fetching_bills, args=(filter, patient_id, callback), daemon=True).start()

def start_online_fetching_bills(filter, pat_id, callback=None):
    if filter == "all":
        url = f"{SERVER_URL}billings/billings/show-all/?hospital_id={store.get('hospital')['hsp_id']}"
    elif filter == "patient":
        url = f"{SERVER_URL}billings/billings/show-patient/?hospital_id={store.get('hospital')['hsp_id']}&patient_id={pat_id}"
    elif filter == "patient-today":
        url = f"{SERVER_URL}billings/billings/show-patient-today/?hospital_id={store.get('hospital')['hsp_id']}&patient_id={pat_id}"
    else:
        return
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
        else:
            data = []
    except Exception:
        data = []

    if callback:
        run_on_main_thread(callback, data)

@mainthread
def run_on_main_thread(callback, data):
    callback(data)