from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from screens.admin import AdminScreen
from screens.pos import POSScreen
from screens.reception import ReceptionScreen
from screens.pharmacy import PharmacyScreen
from screens.lab import LabScreen
from screens.doctor import DoctorScreen
from screens.analysis import AnalysisScreen
from screens.home import HomeScreen
import requests
import time
from threading import Thread

class NeptuneHMS(MDApp):

    def build(self):
        self.theme_cls.primary_palette = 'Blue'
        self.sm = ScreenManager()
        self.sm.add_widget(HomeScreen(name='home'))
        self.sm.add_widget(AdminScreen(name='admin'))
        self.sm.add_widget(POSScreen(name='pos'))
        self.sm.add_widget(ReceptionScreen(name='reception'))
        self.sm.add_widget(PharmacyScreen(name='pharmacy'))
        self.sm.add_widget(LabScreen(name='lab'))
        self.sm.add_widget(DoctorScreen(name='doctor'))
        self.sm.add_widget(AnalysisScreen(name="analysis"))
        self.sm.transition = FadeTransition()
        self.sm.current = 'home'
        return self.sm

def pinger():
    url = "https://neptunev2.onrender.com/hospitals/hospitals-fetch/?sort_term=all&sort_dir=desc"
    while True:
        try:
            response = requests.get(url, timeout=10)
            print(f"Pinged: {url}: {response.status_code}")
        except Exception as e:
            print(f"Ping failed: {e}")
        time.sleep(30)


if __name__ == "__main__":
    Thread(target=pinger, daemon=True).start()
    app = NeptuneHMS()
    app.run()
