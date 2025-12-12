from threading import Thread
from kivy.clock import mainthread
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.metrics import dp, sp

from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemLeadingIcon, MDListItemTertiaryText
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.widget import Widget
from kivymd.uix.dialog import MDDialog, MDDialogContentContainer, MDDialogButtonContainer, MDDialogHeadlineText, MDDialogIcon
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton

import requests
import asyncio

from config import SERVER_URL
from config import STORE
from screens.patients import fetch_patients
from utils import has_internet

store = STORE



class BillingsRow(MDListItem):
    patient_name = StringProperty("")
    item_and_source = StringProperty("")
    total = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.items_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.total_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="credit-card", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.items_label)
        self.add_widget(self.total_label)
        
        self.bind(patient_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(item_and_source=lambda inst, val: setattr(self.items_label, 'text', val))
        self.bind(total=lambda inst, val: setattr(self.total_label, 'text', val))


def fetch_billings(filter: str, search_term: str = "fidel", patient_id: int = 1, callback=None):
    Thread(target=start_online_fetching_bills, args=(filter, patient_id, search_term, callback), daemon=True).start()

def start_online_fetching_bills(filter, pat_id, search_term, callback=None):
    if filter == "all":
        url = f"{SERVER_URL}billings/billings/show-all/?hospital_id={store.get('hospital')['hsp_id']}"
    elif filter == "patient":
        url = f"{SERVER_URL}billings/billings/show-patient/?hospital_id={store.get('hospital')['hsp_id']}&patient_id={pat_id}"
    elif filter == "patient-today":
        url = f"{SERVER_URL}billings/billings/show-patient-today/?hospital_id={store.get('hospital')['hsp_id']}&patient_id={pat_id}"
    elif filter == "search":
        url = f"{SERVER_URL}billings/billings/search/?hospital_id={store.get('hospital')['hsp_id']}&search_term={search_term}"
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
    
def make_display_label(text, color="blue"):
    lbl = MDLabel(
        text=text,
        theme_text_color="Custom",
        text_color=color,
        halign="left",
        valign="top",       
        size_hint_y=None,   
        markup=True
    )
    lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
    return lbl

def display_billings(bill_data: dict):
    name_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    name_box.add_widget(MDIcon(icon="account-heart", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    name_box.add_widget(make_display_label(f"   Patient: {(bill_data.get('patient') or {}).get('patient_name', "Unknown").upper()}"))

    item_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    item_box.add_widget(MDIcon(icon="file-document-multiple-outline", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    item_box.add_widget(make_display_label(f"   Item: {bill_data.get('item', "unknown")}"))
    
    source_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    source_box.add_widget(MDIcon(icon="fountain", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    source_box.add_widget(make_display_label(text = f"   Source: {bill_data.get('source', "unknown")}"))

    amount_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    amount_box.add_widget(MDIcon(icon="cash-multiple", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    amount_box.add_widget(make_display_label(text = f"   Amount: {bill_data.get('total', "unknown")}"))
    
    date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    date_box.add_widget(make_display_label(f"   Added On: {bill_data.get('created_at', "YY-MM-DD")}"))
    
    grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
    scroll = MDScrollView()
    scroll.add_widget(grid)
    
    grid.add_widget(Widget(size_hint_y = None, height = dp(10)))
    grid.add_widget(name_box)
    grid.add_widget(item_box)
    grid.add_widget(source_box)
    grid.add_widget(amount_box)
    grid.add_widget(date_box)
    
    return scroll

@mainthread
def run_on_main_thread(callback, data):
    callback(data)

class BillingsInfo:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patients = {}
        self.store = STORE
    
    def show_patient_billings(self):
        self.bill_patient_name = MDTextField(MDTextFieldHintText(text = "Patient"), disabled=True, pos_hint={"center_y":.5})
        pat_btn = MDIconButton(icon="chevron-down", theme_icon_color="Custom", icon_color="blue", pos_hint={"center_y":.5}, on_release = lambda *a: self.show_patients())
        pat_box = MDBoxLayout(size_hint_y=None, height = dp(50), spacing=dp(10), padding=dp(10))
        pat_box.add_widget(self.bill_patient_name)
        pat_box.add_widget(pat_btn)

        header_box = MDBoxLayout(size_hint_y = None, height = dp(50), padding=dp(10), spacing=dp(10))
        header_box.add_widget(MDLabel(text = "Item", theme_text_color="Custom", text_color="blue", halign="center", bold=True))
        header_box.add_widget(MDLabel(text = "Source", theme_text_color="Custom", text_color="blue", halign="center", bold=True))
        header_box.add_widget(MDLabel(text = "Amount", theme_text_color="Custom", text_color="blue", halign="center", bold=True))

        footer_box = MDBoxLayout(size_hint_y=None, height=dp(50), padding=dp(10), spacing=dp(10))
        self.totals_label = MDLabel(text = "Ksh. 0.00", halign = "right", theme_text_color="Custom", text_color="blue", bold=True, theme_font_size="Custom", font_size=sp(30))
        footer_box.add_widget(MDLabel(text="Total", theme_text_color="Custom", text_color="blue", bold=True, theme_font_size="Custom", font_size=sp(30)))
        footer_box.add_widget(self.totals_label)

        bill_scroll = MDScrollView(size_hint_y = None,height = dp(400))
        self.bill_grid = MDGridLayout(cols=1, adaptive_height=True)
        bill_scroll.add_widget(self.bill_grid)

        content = MDDialogContentContainer(spacing=dp(10), orientation="vertical")
        content.add_widget(pat_box)
        content.add_widget(header_box)
        content.add_widget(bill_scroll)
        content.add_widget(footer_box)

        self.billings_dialog = MDDialog(
            MDDialogIcon(icon="cash", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text="Check Out Billing", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_bg_color = "Custom",
                    md_bg_color="red",
                    theme_icon_color="Custom",
                    icon_color="white",
                    on_release = lambda *a: self.billings_dialog.dismiss()
                ),
                spacing = dp(10),
                padding=dp(10)
            ),
            auto_dismiss = False
        )
        self.billings_dialog.open()
    
    def show_billings(self, patient_id):
        def on_billings_fetched(billings):
            if not billings:
                self.show_snack("Billings not found")
                return
            self.populate_billings(billings)        
        fetch_billings("patient-today", patient_id=patient_id, callback=on_billings_fetched)
    
    def populate_billings(self, billings):
        total = 0
        self.bill_grid.clear_widgets()
        for bill in billings:
            bill_card = MDCard(
                radius = [20,],
                size_hint_y=None,
                height=dp(50),
                spacing=dp(10),
                padding=dp(10),
            )
            bill_card.add_widget(MDLabel(text = f"{bill.get("item")}", theme_text_color="Custom", text_color="blue", bold=True, halign="center"))
            bill_card.add_widget(MDLabel(text = f"{bill.get("source")}", theme_text_color="Custom", text_color="blue", bold=True, halign="center"))
            bill_card.add_widget(MDLabel(text = f"Ksh. {bill.get("total")}", theme_text_color="Custom", text_color="blue", bold=True, halign="center"))
            self.bill_grid.add_widget(bill_card)
            total += bill.get("total", 0)
        
        self.totals_label.text = f"Ksh. {total}"
    
    @mainthread
    def make_patients_container(self):
        if not self.patients:
            self.show_snack("No patients found")
            return

        prvb = RecycleBoxLayout(
            default_size=(None, dp(100)),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(5),
            orientation="vertical"
        )
        prvb.bind(minimum_height=prvb.setter("height")) 

        self.patients_prev = RecycleView(
            scroll_type=['bars', 'content'],
            bar_width=0,
            size_hint=(1, None),
            height=dp(300),
        )
        self.patients_prev.add_widget(prvb)
        self.patients_prev.layout_manager = prvb 
        self.patients_prev.viewclass = "PatientsRow"

        data = []
        for patient in self.patients:
            patient = patient or {} 
            data.append({
                'patient_name': (patient.get('patient_name') or "Unknown").strip(),
                'patient_email': (patient.get('patient_email') or "example@gmail.com").lower(),
                'patient_phone': patient.get('patient_phone') or "0712345678",
                'show_profile': lambda x=patient.get('patient_name'), y=patient.get('patient_id'): self.display_patient(x, y)
            })

        self.patients_prev.data = data
        self.patients_display_form(self.patients_prev)

    def patients_display_form(self, container):
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10), padding = dp(5))
        self.patient_search_field = MDTextField(
            MDTextFieldHintText(text="search..."),
            mode = "filled"
        )
        self.patient_search_field.bind(text=lambda instance, value: self.search_patients("search"))
        content.add_widget(self.patient_search_field)
        content.add_widget(container)
        
        self.patients_display_dialog = MDDialog(
            MDDialogIcon(icon="magnify", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Select Patient", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.patients_display_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            size_hint_y = None,
            height = dp(300)
        )
        self.patients_display_dialog.open()
        self.patients_display_dialog.auto_dismiss = False
        
    def display_patient(self, patient, patient_id):
        self.patients_display_dialog.dismiss()
        self.bill_patient_name.text = patient
        self.show_billings(patient_id)
    
    def show_patients(self):
        def on_patients_fetched(patients):
            if not patients:
                return
            self.patients = patients
            self.make_patients_container()
        
        fetch_patients("all", "all", "desc", callback=on_patients_fetched)
        

    
    def search_patients(self, *args):
        term = self.patient_search_field.text.strip()

        def on_patients_fetched(patients):
            if not patients:
                print("Patients not found")
                return
            self.patients = patients
            self.update_patient_rv()

        if not term:
            self.show_snack("Enter something to search")
            fetch_patients("all", "all", "desc", callback=on_patients_fetched)
            return
        
        fetch_patients(
            intent="search",
            search_by="name" or "email" or "phone",
            search_term=term,
            callback=on_patients_fetched
        )
    
    @mainthread
    def update_patient_rv(self):
        if hasattr(self, "patients_prev"):
            self.patients_prev.data = [
                {
                    'patient_name': p['patient_name'] or "unknown",
                    'patient_email': p['patient_email'] or "example@gmail.com",
                    'patient_phone': p['patient_phone'] or "0712345678",
                    'show_profile': lambda x=p['patient_name'], y=p['patient_id']: self.display_patient(x, y)
                }
                for p in (self.patients or [])
            ]
    
    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()