from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivy.clock import mainthread
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.storage.jsonstore import JsonStore

from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.divider import MDDivider
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemLeadingIcon, MDListItemSupportingText, MDListItemTertiaryText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog, MDDialogButtonContainer, MDDialogContentContainer, MDDialogHeadlineText, MDDialogIcon, MDDialogSupportingText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText, MDTextFieldLeadingIcon
from kivymd.uix.button import MDIconButton
from kivymd.uix.pickers import MDDockedDatePicker
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from threading import Thread
import requests
import asyncio
from datetime import datetime, timedelta
from config import SERVER_URL, STORE
from screens.patients import fetch_patients
from screens.lab_tests import fetch_tests
from database.actions.lab_request import (
    fetch_lab_requests, add_lab_request, 
    delete_lab_request, search_lab_request
)

class RequestsRow(MDListItem):
    patient_name = StringProperty("")
    test = StringProperty("")
    desc = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.test_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.desc_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="clipboard-plus", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.test_label)
        self.add_widget(self.desc_label)
        
        self.bind(patient_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(test=lambda inst, val: setattr(self.test_label, 'text', val))
        self.bind(desc=lambda inst, val: setattr(self.desc_label, 'text', val))

class PatientsRow(MDListItem):
    patient_name = StringProperty("")
    patient_email = StringProperty("")
    patient_phone = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.email_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.phone_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="account-heart", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.email_label)
        self.add_widget(self.phone_label)
        
        self.bind(patient_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(patient_email=lambda inst, val: setattr(self.email_label, 'text', val))
        self.bind(patient_phone=lambda inst, val: setattr(self.phone_label, 'text', val))

class RequestsInfo:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patients = {}
        self.tests = {}
        self.store = STORE
        
    def make_display_label(self, text):
        return MDLabel(
            text = text,
            theme_text_color = "Custom",
            text_color = "blue"
    )

    def display_requests_info(
        self,
        req_data: dict,
    ):
        name_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        name_box.add_widget(MDIcon(icon="account-heart", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        name_box.add_widget(self.make_display_label(f"   Patient: {req_data.get('patient', "Unknown")['patient_name'].upper()}"))

        test_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        test_box.add_widget(MDIcon(icon="flask", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        test_box.add_widget(self.make_display_label(f"   Test: {req_data.get('test', "unknown")['test_name']}"))
        
        desc_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        desc_box.add_widget(MDIcon(icon="information-outline", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        desc_box.add_widget(self.make_display_label(text = f"   About: {req_data.get('test', "unknown")['test_desc']}"))
        
        
        date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        date_box.add_widget(self.make_display_label(f"   Added On: {req_data.get('date_added', "YY-MM-DD")}"))
        
        grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
        scroll = MDScrollView()
        scroll.add_widget(grid)
        
        grid.add_widget(Widget(size_hint_y = None, height = dp(10)))
        grid.add_widget(name_box)
        grid.add_widget(test_box)
        grid.add_widget(desc_box)
        grid.add_widget(date_box)
        
        return scroll

    def fetch_requests(self, intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
        Thread(target=self.fetch_and_return_offline_requests, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()
        #Thread(target=self.fetch_and_return_onlinerequests, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

    def fetch_and_return_online_requests(self, intent, sort_term, sort_dir, search_term, callback):
        url = ""
        if intent == "search":
            url = f"{SERVER_URL}lab_requests/lab_requests-search/?hospital_id={self.store.get('hospital')['hsp_id']}&search_term={search_term}"
        elif intent == "all":
            url = f"{SERVER_URL}lab_requests/lab_requests-fetch/?hospital_id={self.store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
            else:
                data = None
        except Exception:
            data = None

        if callback:
            self.run_on_main_thread(callback, data)
    
    def fetch_and_return_offline_requests(self, intent, sort_term, sort_dir, search_term, callback):
        url = ""
        if intent == "search":
            url = f"{SERVER_URL}lab_requests/lab_requests-search/?hospital_id={self.store.get('hospital')['hsp_id']}&search_term={search_term}"
        elif intent == "all":
            url = f"{SERVER_URL}lab_requests/lab_requests-fetch/?hospital_id={self.store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

        try:
            if intent == "search":
                db_results = asyncio.run(search_lab_request(self.store.get('hospital')['hsp_id'], search_term))
            elif intent == "all":
                db_results = asyncio.run(fetch_lab_requests(self.store.get('hospital')['hsp_id'], sort_term, sort_dir))
            
            data = [
                {
                    "hospital_id": req.hospital_id,
                    "request_id": req.request_id,
                    "test": {
                        "test_id": req.test.test_id,
                        "hospital_id": req.test.hospital_id,
                        "test_name": req.test.test_name,
                        "test_desc": req.test.test_desc,
                        "test_price": req.test.test_price,
                    },
                    "patient": {
                    "patient_id": req.patient.patient_id,
                    "hospital_id": req.patient.hospital_id,
                    "patient_name": req.patient.patient_name,
                    },
                    "date_added": f"{req.date_added}"
                } for req in db_results
            ]

        except Exception:
            data = None

        if callback:
            self.run_on_main_thread(callback, data)

    @mainthread
    def run_on_main_thread(self, callback, data):
        callback(data)

    def requests_add_form(self):
        self.new_patient_name = MDTextField(
            MDTextFieldHintText(text = "Patient"),
            MDTextFieldLeadingIcon(icon="account-heart")
        )
        self.new_test = MDTextField(
            MDTextFieldHintText(text = "Test"),
            MDTextFieldLeadingIcon(icon="flask")
        )
        self.new_patient_id = None
        self.new_test_id = None
        
        name_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        name_box.add_widget(self.new_patient_name)
        name_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_patients()
        )
        name_box.add_widget(name_btn)
        
        test_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        test_box.add_widget(self.new_test)
        test_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_tests()
        )
        test_box.add_widget(test_btn)
        
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(name_box)
        content.add_widget(test_box)
        
        self.requests_dialog = MDDialog(
            MDDialogIcon(icon = "clipboard-plus", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Request Lab Test", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_request_data()
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.requests_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.requests_dialog.open()
        
    def prepare_request_data(self):
        if not self.new_patient_name.text.strip():
            self.show_snack("Enter patient name")
            return
        if not self.new_test.text.strip():
            self.show_snack("Enter test name")
            return
        
        data = {
            "patient_id": self.new_patient_id,
            'test_id': self.new_test_id,
        }
        self.submit_request_data(data)
    def submit_request_data(self, data):
        self.show_snack("Please wait as request is added")
        Thread(target=self.add_request, args=(data,), daemon=True).start()

    def add_request(self, data):
        #url = f"{SERVER_URL}lab_requests/lab_requests-add/?hospital_id={self.store.get('hospital')['hsp_id']}"
        #response = requests.post(url, json=data)
        #if response.status_code != 200:
            #self.show_snack("Failed to add request")
            #return
        #self.show_snack("Request added successfully. You can refresh the page to view them")
        try:
            asyncio.run(add_lab_request(self.store.get('hospital')['hsp_id'], data))
            self.show_snack("Lab request added successfully.")
        except Exception as e:
            self.show_snack("An unexpected error occurred. Please try again.")
            return

    def confirm_deletion_form(self, req_id):
        confirm_delete_dialog = MDDialog(
            MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
            MDDialogHeadlineText(text="Delete Request", theme_text_color="Custom", text_color="red"),
            MDDialogContentContainer(
                MDLabel(
                    text = "Deleting a request is an irreversible process. Are you sure you wish to procede?",
                    theme_text_color = "Custom", text_color = "blue",
                    bold = True, halign="center"
                )
            ),
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.start_request_deletion(req_id)
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: confirm_delete_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
                
        )
        confirm_delete_dialog.open()        

    def start_request_deletion(self, req_id):
        self.show_snack("Please wait as request is deleted")
        Thread(target=self.delete_request, args=(req_id,), daemon=True).start()

    def delete_request(self, req_id):
        #url = f"{SERVER_URL}lab_requests/lab_requests-delete/?hospital_id={self.store.get('hospital')['hsp_id']}&lab_request_id={req_id}"
        #response = requests.delete(url)
        #if response.status_code != 200:
            #self.show_snack("Failed to delete request")
            #return
        #self.show_snack("Request deleted successfully. You can refresh the page to view them")
        try:
            asyncio.run(delete_lab_request(self.store.get('hospital')['hsp_id'], req_id))
            self.show_snack("Lab request deleted successfully")
        except Exception as e:
            self.show_snack("An unexpected error occurred. Please try again")
            return
        
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
            data.append({
                'patient_name': patient['patient_name'] or "unknown",
                'patient_email': patient['patient_email'] or "example@gmail.com",
                'patient_phone': patient['patient_phone'] or "0712345678",
                'show_profile': lambda x=patient['patient_name'], y=patient['patient_id']: self.display_patient(x, y)
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
        self.new_patient_name.text = patient
        self.new_patient_id = patient_id
    
    @mainthread
    def make_tests_container(self):
        if not self.tests:
            self.show_snack("No tests found")
            return

        prvb = RecycleBoxLayout(
            default_size=(None, dp(100)),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(5),
            orientation="vertical"
        )
        prvb.bind(minimum_height=prvb.setter("height")) 

        self.tests_prev = RecycleView(
            scroll_type=['bars', 'content'],
            bar_width=0,
            size_hint=(1, None),
            height=dp(300),
        )
        self.tests_prev.add_widget(prvb)
        self.tests_prev.layout_manager = prvb 
        self.tests_prev.viewclass = "TestsRow"

        data = []
        for test in self.tests:
            data.append({
                'test_name': test['test_name'] or "unknown",
                'test_desc': test['test_desc'] or "unknown",
                'test_price': str(test['test_price']) or "0.0",
                'show_profile': lambda x=test['test_name'], y=test['test_id']: self.display_tests(x, y)
            })

        self.tests_prev.data = data
        self.tests_display_form(self.tests_prev)

    def tests_display_form(self, container):
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10), padding = dp(5))
        self.test_search_field = MDTextField(
            MDTextFieldHintText(text="search..."),
            mode = "filled"
        )
        self.test_search_field.bind(text=lambda instance, value: self.search_tests("search"))
        content.add_widget(self.test_search_field)
        content.add_widget(container)
        
        self.tests_display_dialog = MDDialog(
            MDDialogIcon(icon="magnify", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Select Test", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.tests_display_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            size_hint_y = None,
            height = dp(300)
        )
        self.tests_display_dialog.open()
        self.tests_display_dialog.auto_dismiss = False
        
    def display_tests(self, test, test_id):
        self.tests_display_dialog.dismiss()
        self.new_test.text = test
        self.new_test_id = test_id
    

    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()

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
                for p in self.patients
            ]
    
    def show_tests(self):
        def on_tests_fetched(tests):
            if not tests:
                return
            self.tests = tests
            self.make_tests_container()
        
        fetch_tests("all", "all", "desc", callback=on_tests_fetched)
        

    
    def search_tests(self, *args):
        term = self.test_search_field.text.strip()

        def on_tests_fetched(tests):
            if not tests:
                print("Tests not found")
                return
            self.tests = tests
            self.update_test_rv()

        if not term:
            self.show_snack("Enter something to search")
            fetch_tests("all", "all", "desc", callback=on_tests_fetched)
            return
        
        fetch_tests(
            intent="search",
            search_term=term,
            callback=on_tests_fetched
        )
    
    @mainthread
    def update_test_rv(self):
        if hasattr(self, "tests_prev"):
            self.tests_prev.data = [
                {
                    'test_name': t['test_name'] or "unknown",
                    'test_desc': t['test_desc'] or "unknown",
                    'test_price': str(t['test_price']) or "0.0",
                    'show_profile': lambda x=t['test_name'], y=t['test_id']: self.display_tests(x, y)
                }
                for t in self.tests
            ]