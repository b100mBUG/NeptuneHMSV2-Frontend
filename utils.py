import asyncio
from threading import Thread
from kivy.clock import mainthread
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from config import STORE, SERVER_URL
import requests
import webbrowser


loop = asyncio.new_event_loop()

def start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()

Thread(target=start_loop, daemon=True).start()


def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, loop)



def has_internet(url="https://www.google.com", timeout=5):
    try:
        requests.get(url, timeout=timeout)
        return True
    except Exception:
        return False



class PDFDownloader:
    def __init__(self):
        self.store = STORE

    def download_document(self, source: str | None = None, filter: str | None = None, start_date: str | None = None, end_date: str | None = None, format: str | None = "pdf"):
        Thread(target=self._start_document_download, args=(source, filter, start_date, end_date, format), daemon=True).start()
    
    def _start_document_download(self, source, filter, start_date, end_date, format):
        if source == "patients":
            if format == "pdf":
                url = f"{SERVER_URL}patients/patients-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&filter={filter}"
            else:
                url = f"{SERVER_URL}patients/patients-export-csv?hospital_id={self.store.get('hospital')['hsp_id']}&filter={filter}"
        elif source == "drugs":
            if format == "pdf":
                url = f"{SERVER_URL}drugs/drugs-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&filter={filter}"
            else:
                url = f"{SERVER_URL}drugs/drugs-export-csv?hospital_id={self.store.get('hospital')['hsp_id']}&filter={filter}"
        elif source == "diagnoses":
            if format == "pdf":
                url = f"{SERVER_URL}diagnosis/diagnosis-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
            else:
                url = f"{SERVER_URL}diagnosis/diagnosis-export-csv?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
        elif source == "appointments":
            if format == "pdf":
                url = f"{SERVER_URL}appointments/appointments-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
            else:
                url = f"{SERVER_URL}appointments/appointments-export-csv?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
        elif source == "lab_results":
            if format == "pdf":
                url = f"{SERVER_URL}lab_results/lab_results-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
            else:
                url = f"{SERVER_URL}lab_results/lab_results-export-csv?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
        elif source == "lab_requests":
            if format == "pdf":
                url = f"{SERVER_URL}lab_requests/lab_requests-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
            else:
                url = f"{SERVER_URL}lab_requests/lab_requests-export-csv?hospital_id={self.store.get('hospital')['hsp_id']}&start_date={start_date}&end_date={end_date}"
        else:
            self.show_snack("Unknown document source")
            print(source)
            return
        
        try:
            self.show_snack("Redirecting you to browser for document download...")
            webbrowser.open(url)
        except Exception:
            self.show_snack("An error occurred while staging download. Kindly try again.")


    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text),
            pos_hint={'center_x': 0.5},
            size_hint_x=0.5,
            orientation='horizontal'
        ).open()

