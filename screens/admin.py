from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock, mainthread
from kivy.properties import StringProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.button import MDIconButton, MDButton, MDButtonIcon, MDButtonText
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.widget import Widget
from kivymd.uix.dialog import MDDialog, MDDialogIcon, MDDialogHeadlineText, MDDialogButtonContainer, MDDialogContentContainer, MDDialogSupportingText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText, MDTextFieldLeadingIcon

from screens.patients import (
    display_patients_info,
    fetch_patients,
    patients_add_form,
    patients_edit_form,
)
from screens import patients

from screens.worker import (
    display_workers_info,
    fetch_workers,
    workers_add_form,
    worker_edit_form,
)
from screens import worker

from screens.drugs import (
    display_drugs_info,
    fetch_drugs,
    drugs_add_form,
    drug_edit_form,
    
)
from screens import drugs

from screens.diagnoses import DiagnosisInfo
from screens.prescriptions import PrescriptionsInfo
from screens.services import (
    display_services_info,
    fetch_services,
    service_edit_form,
    services_add_form, 
    
)
from screens import services

from screens.lab_tests import (
    display_tests_info,
    fetch_tests,
    tests_add_form,
    test_edit_form,
)
from screens import lab_tests

from screens import billings
from screens.billings import BillingsInfo

from screens.appointments import AppointmentsInfo
from screens.lab_requests import RequestsInfo
from screens.lab_results import ResultsInfo
from screens.hospital import start_hospital_editing, start_hospital_password_change, start_hospital_deletion

from config import STORE, SERVER_URL, resource_path
from datetime import datetime, timezone, timedelta
from threading import Thread
import requests


Builder.load_file(resource_path("screens/admin.kv"))

class AdminScreen(MDScreen):
    image_path = StringProperty("")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_search_callback = None
        self.ids.search_field.bind(text=self._on_search_field_text)
        self.store = STORE
        self.image_path = resource_path("assets")

    def _on_search_field_text(self, instance, value):
        if self.current_search_callback:
            self.current_search_callback(value)
        
    # Making a universal admin display section...
    def display_items(self, prev_class, items, flag, mapper):
        prev = self.ids.rec_view
        self.ids.rec_box.default_size = (None, dp(80))
        prev.viewclass = prev_class

        data = [mapper(i) for i in items]
        prev.data = data
    
    # Handle mapping, showing and viewing of patients...
    def patients_mapper(self, pat: dict | None):
        pat = pat or {}
        return {
            'patient_name': (pat.get("patient_name") or "Unknown").strip(),
            'patient_email': (pat.get("patient_email") or "example@gmail.com").lower(),
            'patient_phone': pat.get("patient_phone") or "0712345678",
            'show_profile': lambda pat_data=pat: self.display_patients(pat_data)
        }


    def show_patients(self):
        self.current_search_callback = self.search_patients
        self.ids.disp_view.clear_widgets()
        self.show_spinner()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: patients_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_pat_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        
        def on_patients_fetched(patients):
            if not patients:
                self.dismiss_spinner()
                self.show_snack("Patients not found")
                return
            self.dismiss_spinner()
            self.display_items("PatientsRow", patients, "patient", self.patients_mapper)
        
        fetch_patients("all", "all", "desc", callback=on_patients_fetched)

    
    def search_patients(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_patients()
            return

        def on_patients_fetched(patients):
            if not patients:
                print("Patients not found")
                return
            self.display_items("PatientsRow", patients, "patient", self.patients_mapper)

        fetch_patients(
            intent="search",
            search_by="name" or "email" or "phone",
            search_term=term,
            callback=on_patients_fetched
        )
        
    def show_pat_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_patients("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_patients("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_patients("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_patients("Date (Old to New)")
            }
        ]

        self.sort_pat_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_pat_menu.open()
    
    def sort_patients(self, val):
        self.sort_pat_menu.dismiss()
        def on_patients_fetched(patients):
            if not patients:
                self.show_snack("Patients not found")
                return
            self.display_items("PatientsRow", patients, "patient", self.patients_mapper)
        if val == "Name (A to Z)":
            fetch_patients(sort_term="name", sort_dir="asc", callback=on_patients_fetched)
        elif val == "Name (Z to A)":
            fetch_patients(sort_term="name", sort_dir="desc", callback=on_patients_fetched)
        elif val == "Date (New to Old)":
            fetch_patients(sort_term="date", sort_dir="desc", callback=on_patients_fetched)
        elif val == "Date (Old to New)":
            fetch_patients(sort_term="date", sort_dir="asc", callback=on_patients_fetched)
    
    def display_patients(self, pat_data: dict):
        self.preview_display(
            display_patients_info(
                pat_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: patients_edit_form(pat_data)
                ),
                MDLabel(
                    text = "Patients Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: patients.confirm_deletion_form(pat_data.get("patient_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )

    def workers_mapper(self, wrk: dict | None):
        wrk = wrk or {}  
        return {
            'worker_name': (wrk.get("worker_name") or "Unknown").strip(),
            'worker_email': (wrk.get("worker_email") or "example@gmail.com").lower(),
            'worker_phone': wrk.get("worker_phone") or "0712345678",
            'show_profile': lambda wrk_data=wrk: self.display_workers(wrk_data)
        }


    def show_workers(self):
        self.current_search_callback = self.search_workers
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.show_spinner()
        self.ids.add_btn.on_release = lambda *a: workers_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_wrk_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_workers_fetched(workers):
            if not workers:
                self.show_snack("Workers not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("WorkersRow", workers, "worker", self.workers_mapper)
        
        fetch_workers("all", "all", "desc", callback=on_workers_fetched)

    
    def search_workers(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_workers()
            return

        def on_workers_fetched(workers):
            if not workers:
                print("Workers not found")
                return
            self.display_items("WorkersRow", workers, "worker", self.workers_mapper)

        fetch_workers(
            intent="search",
            search_by="name" or "email" or "phone",
            search_term=term,
            callback=on_workers_fetched
        )
        
    def show_wrk_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_workers("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_workers("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_workers("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_workers("Date (Old to New)")
            }
        ]

        self.sort_wrk_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_wrk_menu.open()
    
    def sort_workers(self, val):
        self.sort_wrk_menu.dismiss()
        def on_workers_fetched(workers):
            if not workers:
                self.show_snack("Workers not found")
                return
            self.display_items("WorkersRow", workers, "worker", self.workers_mapper)
        if val == "Name (A to Z)":
            fetch_workers(sort_term="name", sort_dir="asc", callback=on_workers_fetched)
        elif val == "Name (Z to A)":
            fetch_workers(intent="all", sort_term="name", sort_dir="desc", callback=on_workers_fetched)
        elif val == "Date (New to Old)":
            fetch_workers(intent="all", sort_term="date", sort_dir="desc", callback=on_workers_fetched)
        elif val == "Date (Old to New)":
            fetch_workers(sort_term="date", sort_dir="asc", callback=on_workers_fetched)
    
    def display_workers(self, wrk_data: dict):
        self.preview_display(
            display_workers_info(
                wrk_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: worker_edit_form(wrk_data)
                ),
                MDLabel(
                    text = "Worker Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: worker.confirm_deletion_form(wrk_data.get("worker_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    # Making drugs mapper
    def drugs_mapper(self, drug: dict | None):
        drug = drug or {} 
        return {
            'drug_name': (drug.get('drug_name') or "Unknown").strip(),
            'drug_category': (drug.get('drug_category') or "Unknown").strip(),
            'drug_quantity': f"{drug.get('drug_quantity', 0)} available",
            'show_profile': lambda drug_data=drug: self.display_drugs(drug_data)
        }

    def show_drugs(self):
        self.current_search_callback = self.search_drugs
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.show_spinner()
        self.ids.add_btn.on_release = lambda *a: drugs_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_drug_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_drugs_fetched(drugs):
            if not drugs:
                self.show_snack("Drugs not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("DrugsRow", drugs, "worker", self.drugs_mapper)
        
        fetch_drugs("all", "all", "desc", callback=on_drugs_fetched)

    
    def search_drugs(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_drugs()
            return

        def on_drugs_fetched(drugs):
            if not drugs:
                print("Drugs not found")
                return
            self.display_items("DrugsRow", drugs, "drug", self.drugs_mapper)

        fetch_drugs(
            intent="search",
            search_term=term,
            callback=on_drugs_fetched
        )
        
    def show_drug_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_drugs("Date (Old to New)")
            }
        ]

        self.sort_drug_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_drug_menu.open()
    
    def sort_drugs(self, val):
        self.sort_drug_menu.dismiss()
        def on_drugs_fetched(drugs):
            if not drugs:
                self.show_snack("Drugs not found")
                return
            self.display_items("DrugsRow", drugs, "drug", self.drugs_mapper)
        if val == "Name (A to Z)":
            fetch_drugs(sort_term="name", sort_dir="asc", callback=on_drugs_fetched)
        elif val == "Name (Z to A)":
            fetch_drugs(intent="all", sort_term="name", sort_dir="desc", callback=on_drugs_fetched)
        elif val == "Date (New to Old)":
            fetch_drugs(intent="all", sort_term="date", sort_dir="desc", callback=on_drugs_fetched)
        elif val == "Date (Old to New)":
            fetch_drugs(sort_term="date", sort_dir="asc", callback=on_drugs_fetched)
    
    def display_drugs(self, drug_data: dict):
        self.preview_display(
            display_drugs_info(
                drug_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: drug_edit_form(drug_data)
                ),
                MDLabel(
                    text = "Drug Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: drugs.confirm_deletion_form(drug_data.get("drug_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )

    # Making diagnosis mapper
    def diagnosis_mapper(self, diag: dict | None):
        diag = diag or {}
        patient = diag.get("patient") or {}

        return {
            'patient_name': (patient.get("patient_name") or "Unknown").strip(),
            'symptoms': (diag.get("symptoms") or "Unknown").strip(),
            'diagnosis': str(diag.get("suggested_diagnosis") or "Unknown").strip(),
            'show_profile': lambda diag_data=diag: self.display_diagnosis(diag_data)
        }

    def show_diagnosis(self):
        self.current_search_callback = self.search_diagnosis
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: DiagnosisInfo().diagnoses_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_diags_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        def on_diags_fetched(diags):
            if not diags:
                self.show_snack("Diagnosis not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("DiagnosisRow", diags, "diag", self.diagnosis_mapper)
        
        DiagnosisInfo().fetch_diagnoses("all", "all", "desc", callback=on_diags_fetched)

    
    def search_diagnosis(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_diagnosis()
            return

        def on_diags_fetched(diags):
            if not diags:
                print("Diagnosis not found")
                return
            self.display_items("DiagnosisRow", diags, "diag", self.diagnosis_mapper)

        DiagnosisInfo().fetch_diagnoses(
            intent="search",
            search_term=term,
            callback=on_diags_fetched
        )
        
    def show_diags_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_diagnosis("Date (Old to New)")
            }
        ]

        self.sort_diag_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_diag_menu.open()
    
    def sort_diagnosis(self, val):
        self.sort_diag_menu.dismiss()
        def on_diags_fetched(diags):
            if not diags:
                self.show_snack("Diagnosis not found")
                return
            self.display_items("DiagnosisRow", diags, "drug", self.diagnosis_mapper)
        if val == "Name (A to Z)":
            DiagnosisInfo().fetch_diagnoses(sort_term="name", sort_dir="asc", callback=on_diags_fetched)
        elif val == "Name (Z to A)":
            DiagnosisInfo().fetch_diagnoses(intent="all", sort_term="name", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (New to Old)":
            DiagnosisInfo().fetch_diagnoses(intent="all", sort_term="date", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (Old to New)":
            DiagnosisInfo().fetch_diagnoses(sort_term="date", sort_dir="asc", callback=on_diags_fetched)
    
    def display_diagnosis(self, diag_data: dict):
        self.preview_display(
            DiagnosisInfo().display_diagnosis_info(
                diag_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: DiagnosisInfo().diagnosis_edit_form(diag_data)
                ),
                MDLabel(
                    text = "Diagnosis Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: DiagnosisInfo().confirm_deletion_form(diag_data.get("diagnosis_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making prescription mapper
    def prescriptions_mapper(self, presc: dict | None):
        presc = presc or {}
        entries = presc.get('entries') or []

        return {
            'patient_name': (presc.get('patient_name') or "Unknown").strip(),
            'items_count': f"{len(entries)} Items",
            'show_profile': lambda presc_data=presc: self.display_prescriptions(presc_data)
        }

        
    def show_prescriptions(self):
        self.current_search_callback = self.search_prescriptions
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: PrescriptionsInfo().prescriptions_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_prescs_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        def on_prescs_fetched(prescs):
            if not prescs:
                self.show_snack("prescription not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("PrescriptionsRow", prescs, "diag", self.prescriptions_mapper)
        
        PrescriptionsInfo().fetch_prescription("all", "all", "desc", callback=on_prescs_fetched)

    
    def search_prescriptions(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_prescriptions()
            return

        def on_prescs_fetched(prescs):
            if not prescs:
                print("prescription not found")
                return
            self.display_items("PrescriptionsRow", prescs, "diag", self.prescriptions_mapper)

        PrescriptionsInfo().fetch_prescription(
            intent="search",
            search_term=term,
            callback=on_prescs_fetched
        )
        
    def show_prescs_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_prescriptions("Date (Old to New)")
            }
        ]

        self.sort_presc_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_presc_menu.open()
    
    def sort_prescriptions(self, val):
        self.sort_presc_menu.dismiss()
        def on_diags_fetched(diags):
            if not diags:
                self.show_snack("prescription not found")
                return
            self.display_items("PrescriptionsRow", diags, "drug", self.prescriptions_mapper)
        if val == "Name (A to Z)":
            PrescriptionsInfo().fetch_prescription(sort_term="name", sort_dir="asc", callback=on_diags_fetched)
        elif val == "Name (Z to A)":
            PrescriptionsInfo().fetch_prescription(intent="all", sort_term="name", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (New to Old)":
            PrescriptionsInfo().fetch_prescription(intent="all", sort_term="date", sort_dir="desc", callback=on_diags_fetched)
        elif val == "Date (Old to New)":
            PrescriptionsInfo().fetch_prescription(sort_term="date", sort_dir="asc", callback=on_diags_fetched)
    
    def display_prescriptions(self, presc_data: dict):
        self.preview_display(
            PrescriptionsInfo().display_prescriptions_info(
                presc_data
            ),
            MDBoxLayout(
                MDLabel(
                    text = "Presc. Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: PrescriptionsInfo().confirm_deletion_form(presc_data.get("prescription_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making appointment mapper
    def appointments_mapper(self, app: dict | None):
        app = app or {}
        patient = app.get("patient") or {}

        return {
            'patient_name': (patient.get("patient_name") or "Unknown").strip(),
            'app_desc': (app.get("appointment_desc") or "Unknown").strip(),
            'app_date': str(app.get("date_requested") or "YY-MM-DD"),
            'show_profile': lambda app_data=app: self.display_appointments(app_data)
        }


    def show_appointments(self):
        self.current_search_callback = self.search_appointments
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: AppointmentsInfo().apps_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_apps_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        def on_apps_fetched(apps):
            if not apps:
                self.show_snack("Appointments not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("AppointmentsRow", apps, "diag", self.appointments_mapper)
        
        AppointmentsInfo().fetch_apps("all", "all", "desc", callback=on_apps_fetched)

    
    def search_appointments(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_appointments()
            return

        def on_apps_fetched(apps):
            if not apps:
                print("Appointments not found")
                return
            self.display_items("AppointmentsRow", apps, "app", self.appointments_mapper)

        AppointmentsInfo().fetch_apps(
            intent="search",
            search_term=term,
            callback=on_apps_fetched
        )
        
    def show_apps_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_appointments("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_appointments("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_appointments("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_appointments("Date (Old to New)")
            }
        ]

        self.sort_app_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_app_menu.open()
    
    def sort_appointments(self, val):
        self.sort_app_menu.dismiss()
        def on_apps_fetched(apps):
            if not apps:
                self.show_snack("Appointments not found")
                return
            self.display_items("AppointmentsRow", apps, "drug", self.appointments_mapper)
        if val == "Name (A to Z)":
            AppointmentsInfo().fetch_apps(sort_term="name", sort_dir="asc", callback=on_apps_fetched)
        elif val == "Name (Z to A)":
            AppointmentsInfo().fetch_apps(intent="all", sort_term="name", sort_dir="desc", callback=on_apps_fetched)
        elif val == "Date (New to Old)":
            AppointmentsInfo().fetch_apps(intent="all", sort_term="date", sort_dir="desc", callback=on_apps_fetched)
        elif val == "Date (Old to New)":
            AppointmentsInfo().fetch_apps(sort_term="date", sort_dir="asc", callback=on_apps_fetched)
    
    def display_appointments(self, app_data: dict):
        self.preview_display(
            AppointmentsInfo().display_appointments_info(
                app_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: AppointmentsInfo().apps_edit_form(app_data)
                ),
                MDLabel(
                    text = "App. Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: AppointmentsInfo().confirm_deletion_form(app_data.get("appointment_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making services mapper
    def services_mapper(self, service: dict | None):
        service = service or {}

        return {
            'service_name': (service.get("service_name") or "Unknown").strip(),
            'service_desc': (service.get("service_desc") or "Unknown").strip(),
            'service_price': f"Ksh. {service.get('service_price', 0)}",
            'show_profile': lambda service_data=service: self.display_services(service_data)
        }

    def show_services(self):
        self.current_search_callback = self.search_services
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: services_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_service_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        def on_services_fetched(drugs):
            if not drugs:
                self.show_snack("Services not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("ServicesRow", drugs, "service", self.services_mapper)
        
        fetch_services("all", "all", "desc", callback=on_services_fetched)

    
    def search_services(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_services()
            return

        def on_services_fetched(services):
            if not services:
                print("Services not found")
                return
            self.display_items("ServicesRow", services, "drug", self.services_mapper)

        fetch_services(
            intent="search",
            search_term=term,
            callback=on_services_fetched
        )
        
    def show_service_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_services("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_services("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_services("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_services("Date (Old to New)")
            }
        ]

        self.sort_service_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_service_menu.open()
    
    def sort_services(self, val):
        self.sort_service_menu.dismiss()
        def on_services_fetched(services):
            if not services:
                self.show_snack("Services not found")
                return
            self.display_items("ServicesRow", services, "service", self.services_mapper)
        if val == "Name (A to Z)":
            fetch_services(sort_term="name", sort_dir="asc", callback=on_services_fetched)
        elif val == "Name (Z to A)":
            fetch_services(intent="all", sort_term="name", sort_dir="desc", callback=on_services_fetched)
        elif val == "Date (New to Old)":
            fetch_services(intent="all", sort_term="date", sort_dir="desc", callback=on_services_fetched)
        elif val == "Date (Old to New)":
            fetch_services(sort_term="date", sort_dir="asc", callback=on_services_fetched)
    
    def display_services(self, service_data: dict):
        self.preview_display(
            display_services_info(
                service_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: service_edit_form(service_data)
                ),
                MDLabel(
                    text = "Service Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: services.confirm_deletion_form(service_data.get("service_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making tests mapper
    def tests_mapper(self, test: dict | None):
        test = test or {}

        return {
            'test_name': (test.get("test_name") or "Unknown").strip(),
            'test_desc': (test.get("test_desc") or "Unknown").strip(),
            'test_price': f"Ksh. {test.get('test_price', 0)}",
            'show_profile': lambda test_data=test: self.display_tests(test_data)
        }


    def show_tests(self):
        self.current_search_callback = self.search_tests
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: tests_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_test_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        def on_tests_fetched(drugs):
            if not drugs:
                self.show_snack("tests not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("TestsRow", drugs, "test", self.tests_mapper)
        
        fetch_tests("all", "all", "desc", callback=on_tests_fetched)

    
    def search_tests(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_tests()
            return

        def on_tests_fetched(tests):
            if not tests:
                print("tests not found")
                return
            self.display_items("TestsRow", tests, "drug", self.tests_mapper)

        fetch_tests(
            intent="search",
            search_term=term,
            callback=on_tests_fetched
        )
        
    def show_test_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_tests("Date (Old to New)")
            }
        ]

        self.sort_test_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_test_menu.open()
    
    def sort_tests(self, val):
        self.sort_test_menu.dismiss()
        def on_tests_fetched(tests):
            if not tests:
                self.show_snack("tests not found")
                return
            self.display_items("TestsRow", tests, "test", self.tests_mapper)
        if val == "Name (A to Z)":
            fetch_tests(sort_term="name", sort_dir="asc", callback=on_tests_fetched)
        elif val == "Name (Z to A)":
            fetch_tests(intent="all", sort_term="name", sort_dir="desc", callback=on_tests_fetched)
        elif val == "Date (New to Old)":
            fetch_tests(intent="all", sort_term="date", sort_dir="desc", callback=on_tests_fetched)
        elif val == "Date (Old to New)":
            fetch_tests(sort_term="date", sort_dir="asc", callback=on_tests_fetched)
    
    def display_tests(self, test_data: dict):
        self.preview_display(
            display_tests_info(
                test_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: test_edit_form(test_data)
                ),
                MDLabel(
                    text = "test Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: lab_tests.confirm_deletion_form(test_data.get("test_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Making requests mapper
    def requests_mapper(self, request: dict | None):
        request = request or {}
        patient = request.get("patient") or {}
        test = request.get("test") or {}

        return {
            'patient_name': (patient.get("patient_name") or "Unknown").strip(),
            'test': (test.get("test_name") or "Unknown").strip(),
            'desc': (test.get("test_desc") or "Unknown").strip(),
            'show_profile': lambda request_data=request: self.display_requests(request_data)
        }


    def show_requests(self):
        self.current_search_callback = self.search_requests
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: RequestsInfo().requests_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_request_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        def on_requests_fetched(drugs):
            if not drugs:
                self.show_snack("Requests not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("RequestsRow", drugs, "request", self.requests_mapper)
        
        RequestsInfo().fetch_requests("all", "all", "desc", callback=on_requests_fetched)

    
    def search_requests(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_requests()
            return

        def on_requests_fetched(requests):
            if not requests:
                print("Requests not found")
                return
            self.display_items("RequestsRow", requests, "drug", self.requests_mapper)

        RequestsInfo().fetch_requests(
            intent="search",
            search_term=term,
            callback=on_requests_fetched
        )
        
    def show_request_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_requests("Date (Old to New)")
            }
        ]

        self.sort_request_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_request_menu.open()
    
    def sort_requests(self, val):
        self.sort_request_menu.dismiss()
        def on_requests_fetched(requests):
            if not requests:
                self.show_snack("requests not found")
                return
            self.display_items("RequestsRow", requests, "request", self.requests_mapper)
        if val == "Name (A to Z)":
            RequestsInfo().fetch_requests(sort_term="name", sort_dir="asc", callback=on_requests_fetched)
        elif val == "Name (Z to A)":
            RequestsInfo().fetch_requests(intent="all", sort_term="name", sort_dir="desc", callback=on_requests_fetched)
        elif val == "Date (New to Old)":
            RequestsInfo().fetch_requests(intent="all", sort_term="date", sort_dir="desc", callback=on_requests_fetched)
        elif val == "Date (Old to New)":
            RequestsInfo().fetch_requests(sort_term="date", sort_dir="asc", callback=on_requests_fetched)
    
    def display_requests(self, req_data: dict):
        self.preview_display(
            RequestsInfo().display_requests_info(
                req_data
            ),
            MDBoxLayout(
                MDLabel(
                    text = "Lab Request Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: RequestsInfo().confirm_deletion_form(req_data.get("request_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )

    # Making results mapper
    def results_mapper(self, result: dict | None):
        result = result or {}
        patient = result.get("patient") or {}

        return {
            'patient_name': (patient.get("patient_name") or "Unknown").strip(),
            'observations': (result.get("observations") or "Unknown").strip(),
            'conclusions': str(result.get("conclusion") or "Unknown").strip(),
            'show_profile': lambda result_data=result: self.display_results(result_data)
        }


    def show_results(self):
        self.current_search_callback = self.search_results
        self.ids.disp_view.clear_widgets()
        self.ids.sort_btn.disabled = False
        self.ids.add_btn.on_release = lambda *a: ResultsInfo().results_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_result_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        def on_results_fetched(drugs):
            if not drugs:
                self.show_snack("Results not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("ResultsRow", drugs, "result", self.results_mapper)
        
        ResultsInfo().fetch_results("all", "all", "desc", callback=on_results_fetched)

    
    def search_results(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_results()
            return

        def on_results_fetched(results):
            if not results:
                print(result)
                print("results not found")
                return
            self.display_items("ResultsRow", results, "drug", self.results_mapper)

        ResultsInfo().fetch_results(
            intent="search",
            search_term=term,
            callback=on_results_fetched
        )
        
    def show_result_sort_dropdown(self, caller):
        drop_down_items = [
            {
                "text": "Name (A to Z)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Name (A to Z)")
            },
            {
                "text": "Name (Z to A)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Name (Z to A)")
            },
            {
                "text": "Date (New to Old)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-male",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Date (New to Old)")
            },
            {
                "text": "Date (Old to New)",
                "theme_text_color": "Custom",
                "text_color": "blue",
                "bold": True,
                "icon": "gender-female",
                "theme_icon_color": "Custom",
                "icon_color": "blue",
                "on_release": lambda *a: self.sort_results("Date (Old to New)")
            }
        ]

        self.sort_result_menu = MDDropdownMenu(
            caller=caller,
            items=drop_down_items,
            width_mult=4
        )
        self.sort_result_menu.open()
    
    def sort_results(self, val):
        self.sort_result_menu.dismiss()
        def on_results_fetched(results):
            if not results:
                self.show_snack("results not found")
                return
            self.display_items("ResultsRow", results, "result", self.results_mapper)
        if val == "Name (A to Z)":
            ResultsInfo().fetch_results(sort_term="name", sort_dir="asc", callback=on_results_fetched)
        elif val == "Name (Z to A)":
            ResultsInfo().fetch_results(intent="all", sort_term="name", sort_dir="desc", callback=on_results_fetched)
        elif val == "Date (New to Old)":
            ResultsInfo().fetch_results(intent="all", sort_term="date", sort_dir="desc", callback=on_results_fetched)
        elif val == "Date (Old to New)":
            ResultsInfo().fetch_results(sort_term="date", sort_dir="asc", callback=on_results_fetched)
    
    def display_results(self, res_data: dict):
        self.preview_display(
            ResultsInfo().display_results_info(
                res_data
            ),
            MDBoxLayout(
                MDIconButton(
                    icon = "pencil-outline",
                    theme_icon_color = "Custom",
                    icon_color = "blue",
                    on_release = lambda *a: ResultsInfo().result_edit_form(res_data)
                ),
                MDLabel(
                    text = "Lab result Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                MDIconButton(
                    icon = "trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "red",
                    on_release = lambda *a: ResultsInfo().confirm_deletion_form(res_data.get("result_id"))
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )
    
    # Handle mapping, showing and viewing of patients...
    def billings_mapper(self, bill: dict | None):
        bill = bill or {}
        patient = bill.get("patient") or {}  
        return {
            'patient_name': (patient.get("patient_name") or "OTC").strip(),
            'item_and_source': f"{(bill.get('item') or 'item').lower()} | {(bill.get('source') or 'source')}",
            'total': f"{bill.get('total') or '0'}",
            'show_profile': lambda bill_data=bill: self.display_billings(bill_data)
        }

    
    def show_billings(self):
        self.current_search_callback = self.search_billings
        self.ids.disp_view.clear_widgets()
        self.ids.add_btn.on_release = lambda *a: BillingsInfo().show_patient_billings()
        self.ids.sort_btn.disabled = True
        self.ids.rec_box.clear_widgets()
        self.show_spinner()
        
        def on_billings_fetched(billings):
            if not billings:
                self.show_snack("Billings not found")
                self.dismiss_spinner()
                return
            self.dismiss_spinner()
            self.display_items("BillingsRow", billings, "billings", self.billings_mapper)
        
        billings.fetch_billings("all", "", callback=on_billings_fetched)
    
    def search_billings(self, *args):
        term = self.ids.search_field.text.strip()
        if not term:
            self.show_snack("Enter something to search")
            self.show_billings()
            return

        def on_billings_fetched(billings):
            if not billings:
                print("Billings not found")
                return
            self.display_items("BillingsRow", billings, "billings", self.billings_mapper)

        billings.fetch_billings(filter="search", search_term=term, callback=on_billings_fetched)
    
    def display_billings(self, bill_data: dict):
        self.preview_display(
            billings.display_billings(
                bill_data
            ),
            MDBoxLayout(
                MDLabel(
                    text = "Billing Preview",
                    size_hint_y = None,
                    height = dp(50),
                    theme_font_size = "Custom",
                    font_size = "28sp",
                    theme_text_color = "Custom", 
                    text_color = "blue",
                    halign = "center",
                    bold = True
                ),
                spacing = dp(10),
                padding = dp(10),
                size_hint_y = None,
                height = dp(55)
            )
        )

    def settings_form(self):
        self.hosp_edit_name = MDTextField(
            MDTextFieldLeadingIcon(
                icon="bank",
            ),
            MDTextFieldHintText(text = "Hospital Name"),
            text = self.store.get("hospital")['name']
        )
        self.hosp_edit_email = MDTextField(
            MDTextFieldLeadingIcon(
                icon="gmail",
            ),
            MDTextFieldHintText(text = "Hospital Email"),
            text = self.store.get("hospital")['email']
        )
        self.hosp_edit_phone = MDTextField(
            MDTextFieldLeadingIcon(
                icon="phone",
            ),
            MDTextFieldHintText(text = "Hospital Phone"),
            text = self.store.get("hospital")['phone']
        )
        self.hosp_diag_edit = MDTextField(
            MDTextFieldLeadingIcon(
                icon="currency-usd",
            ),
            MDTextFieldHintText(text = "Diagnosis Fee"),
            text = str(self.store.get("hospital")['diag_fee']),
            input_filter = "float"
        )
        
        self.current_hosp_password = MDTextField(
            MDTextFieldLeadingIcon(
                icon="key",
            ),
            MDTextFieldHintText(text = "Current Password")
        )
        self.new_hosp_password = MDTextField(
            MDTextFieldLeadingIcon(
                icon="key",
            ),
            MDTextFieldHintText(text = "New Password")
        )
        self.new_hosp_password_confirm = MDTextField(
            MDTextFieldLeadingIcon(
                icon="key",
            ),
            MDTextFieldHintText(text = "Confirm New Password")
        )
        content = MDDialogContentContainer(spacing = dp(10), padding=dp(10))
        grid = MDGridLayout(cols=1, spacing=dp(10), adaptive_height=True)
        scroll = MDScrollView(size_hint_y = None, height = dp(400))
        scroll.add_widget(grid)
        content.add_widget(scroll)
        
        grid.add_widget(
            MDLabel(
                text = "Edit Hospital Detail",
                halign = "center",
                theme_text_color = "Custom",
                text_color = "blue",
                size_hint_y = None,
                height = dp(30),
                bold = True,
                theme_font_size = "Custom",
                font_size = "25sp"
                
            )
        )
        grid.add_widget(self.hosp_edit_name)
        grid.add_widget(self.hosp_edit_email)
        grid.add_widget(self.hosp_edit_phone)
        grid.add_widget(self.hosp_diag_edit)
        
        grid.add_widget(
            MDIconButton(
                icon="pencil-outline",
                theme_icon_color = "Custom",
                icon_color = "white",
                theme_bg_color = "Custom",
                md_bg_color = "green",
                on_release = lambda *a: self.prepare_hospital_data()
            )
        )
        
        grid.add_widget(
            MDLabel(
                text = "Edit Hospital Credentials",
                halign = "center",
                theme_text_color = "Custom",
                text_color = "blue",
                size_hint_y = None,
                height = dp(30),
                bold = True,
                theme_font_size = "Custom",
                font_size = "25sp"
                
            )
        )
        grid.add_widget(self.current_hosp_password)
        grid.add_widget(self.new_hosp_password)
        grid.add_widget(self.new_hosp_password_confirm)
        check = MDCheckbox(
            size_hint = (None, None),
            size = (dp(40), dp(40)),
            size_hint_x = 0.1,
            pos_hint = {"center_y": .5},
            on_active =  lambda *a: self.toggle_show_hsp_pass(check.active)
        )
        grid.add_widget(
            MDBoxLayout(
                check,
                MDLabel(
                    text = "Show password?",
                    size_hint_x = 0.9,
                    theme_text_color = "Custom",
                    text_color = "blue"
                ),
                spacing = dp(10),
                size_hint_y = None,
                height = dp(40)
            )
        )
        
        grid.add_widget(
            MDIconButton(
                icon="check",
                theme_icon_color = "Custom",
                icon_color = "white",
                theme_bg_color = "Custom",
                md_bg_color = "green",
                on_release = lambda *a: self.prepare_password_data()
                
            )
        )
        
        grid.add_widget(
            MDLabel(
                text = "Delete Hospital Account",
                halign = "center",
                theme_text_color = "Custom",
                text_color = "blue",
                size_hint_y = None,
                height = dp(30),
                bold = True,
                theme_font_size = "Custom",
                font_size = "25sp"
                
            )
        )
        grid.add_widget(
            MDButton(
                MDButtonIcon(
                    icon="trash-can",
                    theme_icon_color = "Custom",
                    icon_color = "white"
                ),
                MDButtonText(
                    text = "Delete Account",
                    theme_text_color = "Custom",
                    text_color = "white",
                ),
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: self.prepare_delete_data()
            )
        )
        
        self.settings_dialog = MDDialog(
            MDDialogIcon(icon = "cog", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Settings", theme_text_color = "Custom", text_color = "blue"),
            MDDialogSupportingText(text = "Modify your hospital details", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon = "close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.settings_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            auto_dismiss = False
        )
        self.settings_dialog.open()
        
    def toggle_show_hsp_pass(self, value):
        if value:
            self.new_hosp_password.password = False
            self.current_hosp_password.password = False
            self.new_hosp_password_confirm.password = False
        else:
            self.new_hosp_password.password = True
            self.current_hosp_password.password = True
            self.new_hosp_password_confirm.password = True
            
    def prepare_hospital_data(self):
        hosp_name = self.hosp_edit_name.text.strip()
        hosp_email = self.hosp_edit_email.text.strip()
        hosp_phone = self.hosp_edit_phone.text.strip()
        hosp_diag_fee = float(self.hosp_diag_edit.text.strip())
        
        hosp_data = {
            "hospital_name": hosp_name,
            "hospital_email": hosp_email,
            "hospital_contact": hosp_phone,
            "diagnosis_fee": float(hosp_diag_fee)
        }
        
        start_hospital_editing(hosp_data, callback=self.on_hsp_edit_success)
    
    def on_hsp_edit_success(self, hsp_data):
        self.settings_dialog.dismiss()
        if not self.store.exists("hospital"):
            return
        self.store.delete("hospital")
        self.store.put(
            "hospital", 
            hsp_id=hsp_data.get("hospital_id"),
            name=hsp_data.get("hospital_name"), 
            email=hsp_data.get("hospital_email"), 
            phone=hsp_data.get("hospital_contact"),
            diag_fee=hsp_data.get("diagnosis_fee"),
            expiry_date=hsp_data.get("expiry_date")
        )
    
    def prepare_password_data(self):
        former_password = self.current_hosp_password.text.strip()
        new_password = self.new_hosp_password.text.strip()
        new_confirm = self.new_hosp_password_confirm.text.strip()
        
        if not former_password:
            self.show_snack("Enter current password")
            return
        
        if not new_password:
            self.show_snack("Enter new password")
            return
        
        if not new_confirm:
            self.show_snack("Confirm new password")
            return
        
        if new_confirm != new_password:
            self.show_snack("Password confirmation missmatch")
            return
        
        hosp_data = {
            "former_password": former_password,
            "new_password": new_password,
        }
        
        start_hospital_password_change(hosp_data, callback=self.on_pwd_change_success)
    
    def on_pwd_change_success(self):
        self.settings_dialog.dismiss()
    
    def prepare_delete_data(self):  
        start_hospital_deletion(callback=self.on_hsp_delete_success)
    
    def on_pwd_change_success(self):
        self.settings_dialog.dismiss()

    def on_hsp_delete_success(self):
        self.settings_dialog.dismiss()
        self.store.delete("hospital")
        
        app = MDApp()
        app.stop()

    
    def make_disp_label(self, text, color):
        return MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=color,
            bold=True,
            halign="center",
            theme_font_size="Custom",
            font_size="24sp",
            size_hint_y=None,
            height=dp(30)
        )

    def plan_form(self):
        disp_grid = MDGridLayout(spacing=dp(5), padding=dp(5), cols=6, adaptive_height=True)

        for text in ["YRS", "MTHS", "DYS", "HRS", "MINS", "SECS"]:
            disp_grid.add_widget(self.make_disp_label(text, "blue"))

        self.val_labels = []
        for _ in range(6):
            lbl = self.make_disp_label("00", "green")
            self.val_labels.append(lbl)
            disp_grid.add_widget(lbl)

        content = MDDialogContentContainer(spacing=dp(10), orientation="vertical")
        content.add_widget(self.make_disp_label("Your plan expires in:", "red"))
        content.add_widget(disp_grid)
        content.add_widget(self.make_disp_label("Renew your plan today:", "blue"))

        self.renew_plan_field = MDTextField(MDTextFieldHintText(text="Enter Access Key: "), on_text_validate = lambda *a: self.renew_plan())
        content.add_widget(self.renew_plan_field)

        self.plan_dialog = MDDialog(
            MDDialogIcon(
                icon="information-outline",
                theme_icon_color="Custom",
                icon_color="blue"
            ),
            MDDialogHeadlineText(
                text="Plan Information",
                theme_text_color="Custom",
                text_color="blue"
            ),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color="Custom",
                    icon_color="white",
                    theme_bg_color="Custom",
                    md_bg_color="red",
                    on_release=lambda *a: self.dismiss_plan_dialog()
                ),
                spacing=dp(10),
                padding=dp(10)
            ),
            auto_dismiss=False
        )

        self.plan_dialog.open()

        self.countdown_event = Clock.schedule_interval(self.update_countdown, 1)


    def dismiss_plan_dialog(self):
        if hasattr(self, "countdown_event"):
            Clock.unschedule(self.countdown_event)
        self.plan_dialog.dismiss()

    def update_countdown(self, dt):
        if not self.store.exists("hospital"):
            return

        expiry_str = self.store.get("hospital")['expiry_date']
        expiry = datetime.fromisoformat(expiry_str)  

        KENYA_TZ = timezone(timedelta(hours=3))
        expiry = expiry.replace(tzinfo=KENYA_TZ)

        now = datetime.now(KENYA_TZ)
        remaining = expiry - now

        if remaining.total_seconds() <= 0:
            for lbl in self.val_labels:
                lbl.text = "00"
            self.show_snack("Your plan has expired!")
            return

        total_seconds = int(remaining.total_seconds())
        days_total, rem_secs = divmod(total_seconds, 86400)
        years, days_remain = divmod(days_total, 365)
        months, days = divmod(days_remain, 30)
        hours, rem_secs = divmod(rem_secs, 3600)
        mins, secs = divmod(rem_secs, 60)

        parts = [years, months, days, hours, mins, secs]

        for lbl, val in zip(self.val_labels, parts):
            lbl.text = f"{val:02d}"


    
    def help_form(self):
        self.help_desc = MDTextField(
            MDTextFieldHintText(
                text = "Describe your issue"
            ),
            size_hint_y = None,
            height = dp(100),
            multiline = True
        )
        self.help_dialog  = MDDialog(
            MDDialogIcon(icon = "help", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Feel Stuck?", theme_text_color = "Custom", text_color = "blue"),
            MDDialogSupportingText(text = "Get help from us.", theme_text_color = "Custom", text_color = "blue"),
            MDDialogContentContainer(
                self.help_desc,
                MDGridLayout(
                    Widget(),
                    MDIconButton(
                        icon = "whatsapp",
                        theme_icon_color = "Custom",
                        icon_color = "white",
                        theme_bg_color = "Custom",
                        md_bg_color = "green"
                    ),
                    MDIconButton(
                        icon = "gmail",
                        theme_icon_color = "Custom",
                        icon_color = "white",
                        theme_bg_color = "Custom",
                        md_bg_color = "brown"
                    ),
                    MDIconButton(
                        icon = "facebook",
                        theme_icon_color = "Custom",
                        icon_color = "white",
                        theme_bg_color = "Custom",
                        md_bg_color = "blue"
                    ),
                    MDIconButton(
                        icon = "instagram",
                        theme_icon_color = "Custom",
                        icon_color = "white",
                        theme_bg_color = "Custom",
                        md_bg_color = "magenta"
                    ),
                    Widget(),
                    cols = 6,
                    spacing = dp(10),
                    adaptive_height = True
                ),
                spacing = dp(35),
                padding = dp(10),
                orientation = "vertical"
            ),
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon = "close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.help_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            auto_dismiss = False
        )
        self.help_dialog.open()
    
    def renew_plan(self):
        key = self.renew_plan_field.text.strip()
        if not key:
            self.show_snack("Activation key empty!")
            return
        Thread(target=self.start_plan_renewal, args=(key,), daemon=True).start()


    def start_plan_renewal(self, key):
        try:
            url = f"{SERVER_URL}hospitals/renew-activation/?hospital_id={self.store.get('hospital')['hsp_id']}&activation_key={key}"
            response = requests.put(url, timeout=3).json()

            if response.get("message") == "renewed":
                self.plan_dialog.dismiss()
                self.show_snack("Your plan renewed! Enjoy :-)")
                self.update_plan()
            else:
                self.show_snack(response.get("message", "Renewal failed"))
        except Exception as e:
            self.show_snack(f"Error: {e}")


    def update_plan(self):
        Thread(target=self.start_plan_update, daemon=True).start()


    def start_plan_update(self):
        try:
            if not self.store.exists("hospital"):
                return

            url = f"{SERVER_URL}hospitals/hospitals-specific/?hospital_id={self.store.get('hospital')['hsp_id']}"
            response = requests.get(url)

            if response.status_code != 200:
                self.show_snack("Failed to update plan")
                return

            hsp_data = response.json()
            if not hsp_data:
                self.show_snack("Invalid response data")
                return

            self.show_snack("Updating hospital plan...")
            self.store.put(
                "hospital",
                hsp_id=hsp_data.get("hospital_id"),
                name=hsp_data.get("hospital_name"),
                email=hsp_data.get("hospital_email"),
                phone=hsp_data.get("hospital_contact"),
                diag_fee=hsp_data.get("diagnosis_fee"),
                expiry_date=hsp_data.get("expiry_date"),
            )
            self.show_snack("Plan updated successfully!")
        except Exception as e:
            self.show_snack(f"Error updating plan: {e}")
    
    # Making a universal custom item preview 
    def preview_display(self, container, prev_header):
        self.ids.disp_view.clear_widgets()
        self.ids.disp_view.add_widget(prev_header)
        self.ids.disp_view.add_widget(container)
    
    @mainthread
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()
    @mainthread
    def show_spinner(self, display_text: str | None = "Please wait as data is fetched..."):
        spinner = MDCircularProgressIndicator(
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            size_hint=(None, None),
            size=(dp(48), dp(48)),
        )
        self.spinner_dialog = MDDialog(
            MDDialogIcon(icon="clock", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Loading...", theme_text_color = "Custom", text_color="blue", bold=True),
            MDDialogSupportingText(text= display_text, theme_text_color = "Custom", text_color="blue"),
            MDDialogContentContainer(
                spinner,
                orientation="vertical"
            ),
            auto_dismiss = False
        )
        self.spinner_dialog.open()
    
    @mainthread
    def dismiss_spinner(self):
        self.spinner_dialog.dismiss()