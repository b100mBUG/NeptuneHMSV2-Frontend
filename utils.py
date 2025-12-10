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

    def download_document(self, source, filter):
        Thread(target=self._start_document_download, args=(source, filter), daemon=True).start()
    
    def _start_document_download(self, source, filter):
        if source == "patients":
            url = f"{SERVER_URL}patients/patients-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&filter={filter}"
        elif source == "drugs":
            url = f"{SERVER_URL}drugs/drugs-export-pdf?hospital_id={self.store.get('hospital')['hsp_id']}&filter={filter}"
        else:
            self.show_snack("Unknown document source")
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

