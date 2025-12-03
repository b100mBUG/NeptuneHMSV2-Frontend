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
from datetime import datetime, timedelta
from config import SERVER_URL
from screens.patients import fetch_patients
from config import STORE

class DiagnosisRow(MDListItem):
    patient_name = StringProperty("")
    symptoms = StringProperty("")
    diagnosis = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.symptoms_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.diagnosis_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="stethoscope", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.symptoms_label)
        self.add_widget(self.diagnosis_label)
        
        self.bind(patient_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(symptoms=lambda inst, val: setattr(self.symptoms_label, 'text', val))
        self.bind(diagnosis=lambda inst, val: setattr(self.diagnosis_label, 'text', val))

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

class DiagnosisInfo:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patients = {}
        self.store = STORE
        
    def make_display_label(self, text, color="blue"):
        lbl = MDLabel(
            text=text,
            theme_text_color="Custom",
            text_color=color,
            halign="left",
            adaptive_height = True,
        )
        return lbl

    def display_diagnosis_info(
        self,
        diag_data: dict,
    ):
        name_box = MDBoxLayout(spacing = dp(5), adaptive_height = True)
        name_box.add_widget(MDIcon(icon="account-heart", pos_hint = {"top":1}, theme_icon_color = "Custom", icon_color = "blue"))
        name_box.add_widget(self.make_display_label(f"Patient: {diag_data.get('patient', "Unknown")['patient_name'].upper()}"))

        symptoms_box = MDBoxLayout(spacing = dp(5), adaptive_height = True)
        symptoms_box.add_widget(MDIcon(icon="medical-bag", pos_hint = {"top":1}, theme_icon_color = "Custom", icon_color = "blue"))
        symptoms_box.add_widget(self.make_display_label(f"Symptoms: {diag_data.get('symptoms', "unknown")}"))
        
        findings_box = MDBoxLayout(spacing = dp(5), adaptive_height = True)
        findings_box.add_widget(MDIcon(icon="microscope", pos_hint = {"top":1}, theme_icon_color = "Custom", icon_color = "blue"))
        findings_box.add_widget(self.make_display_label(text = f"Findings: {diag_data.get('findings', "unknown")}"))
        
        diagnosis_box = MDBoxLayout(spacing = dp(5), adaptive_height = True)
        diagnosis_box.add_widget(MDIcon(icon="clipboard-pulse-outline", pos_hint = {"top":1}, theme_icon_color = "Custom", icon_color = "blue"))
        diagnosis_box.add_widget(self.make_display_label(text = f"   Diagnosis: {diag_data.get('suggested_diagnosis', "0712345678")}"))
        
        
        date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        date_box.add_widget(self.make_display_label(f"Added On: {diag_data.get('date_added', "YY-MM-DD")}"))
        
        grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
        scroll = MDScrollView()
        scroll.add_widget(grid)
        
        grid.add_widget(Widget(size_hint_y = None, height = dp(30)))
        grid.add_widget(name_box)
        grid.add_widget(symptoms_box)
        grid.add_widget(findings_box)
        grid.add_widget(diagnosis_box)
        grid.add_widget(date_box)
        
        return scroll

    def fetch_diagnoses(self, intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
        Thread(target=self.fetch_and_return_diagnoses, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

    def fetch_and_return_diagnoses(self, intent, sort_term, sort_dir, search_term, callback):
        url = ""
        if intent == "search":
            url = f"{SERVER_URL}diagnosis/diagnosis-search/?hospital_id={self.store.get('hospital')['hsp_id']}&search_term={search_term}"
        elif intent == "all":
            url = f"{SERVER_URL}diagnosis/diagnosis-fetch/?hospital_id={self.store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

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

    @mainthread
    def run_on_main_thread(self, callback, data):
        callback(data)

    def diagnoses_add_form(self):
        self.new_patient_name = MDTextField(
            MDTextFieldHintText(text = "Patient"),
            MDTextFieldLeadingIcon(icon="account-heart")
        )
        self.new_symptoms = MDTextField(
            MDTextFieldHintText(text = "Symptoms"),
            MDTextFieldLeadingIcon(icon="medical-bag")
        )
        self.new_findings = MDTextField(
            MDTextFieldHintText(text = "Findings"),
            MDTextFieldLeadingIcon(icon="microscope")
        )
        self.new_diagnoses = MDTextField(
            MDTextFieldHintText(text = "Diagnosis"),
            MDTextFieldLeadingIcon(icon="clipboard-pulse-outline")
        )
        self.new_patient_id = None
        
        name_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        name_box.add_widget(self.new_patient_name)
        name_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_patients()
        )
        name_box.add_widget(name_btn)
        
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(name_box)
        content.add_widget(self.new_symptoms)
        content.add_widget(self.new_findings)
        content.add_widget(self.new_diagnoses)
        
        self.diagnosis_dialog = MDDialog(
            MDDialogIcon(icon = "stethoscope", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Add Diagnosis", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_diagnosis_data()
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.diagnosis_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.diagnosis_dialog.open()
        
    def prepare_diagnosis_data(self):
        if not self.new_patient_name.text.strip():
            self.show_snack("Enter patient name")
            return
        if not self.new_symptoms.text.strip():
            self.show_snack("Enter symptoms")
            return
        if not self.new_findings.text.strip():
            self.show_snack("Enter findings")
            return
        if not self.new_diagnoses.text.strip():
            self.show_snack("Enter diagnosis")
            return
        
        data = {
            "patient_id": self.new_patient_id,
            'symptoms': self.new_symptoms.text.strip(),
            'findings': self.new_findings.text.strip(),
            'suggested_diagnosis': self.new_diagnoses.text.strip()
        }
        self.submit_diagnosis_data(data)
    def submit_diagnosis_data(self, data):
        self.show_snack("Please wait as diagnosis is added")
        Thread(target=self.add_diagnosis, args=(data,), daemon=True).start()

    def add_diagnosis(self, data):
        url = f"{SERVER_URL}diagnosis/diagnosis-add/?hospital_id={self.store.get('hospital')['hsp_id']}"
        response = requests.post(url, json=data)
        if response.status_code != 200:
            self.show_snack("Failed to add diagnosis")
            return
        self.show_snack("Diagnosis added successfully. You can refresh the page to view them")

    def make_text_field(self, field_name, field_icon, field_text=None):
        text_field = MDTextField(
            MDTextFieldHintText(text=field_name),
            MDTextFieldLeadingIcon(icon=field_icon),
            text=str(field_text or "")
        )
        return text_field

    def diagnosis_edit_form(self, diag: dict):
        self.edit_symptoms = self.make_text_field("Symptoms", "medical-bag", diag.get("symptoms", None))
        self.edit_findings = self.make_text_field("Findings", "microscope", diag.get("findings", None))
        self.edit_diagnoses = self.make_text_field("Diagnoses", "clipboard-pulse-outline", diag.get("suggested_diagnosis", None))   

        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(self.edit_symptoms)
        content.add_widget(self.edit_findings)
        content.add_widget(self.edit_diagnoses)
        
        self.diagnosis_edit_dialog = MDDialog(
            MDDialogIcon(icon = "stethoscope", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Edit Diagnosis", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_diagnosis_edit_data(diag.get('diagnosis_id'))
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.diagnosis_edit_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.diagnosis_edit_dialog.open()
        

    def prepare_diagnosis_edit_data(self, diag_id):
        
        data = {
            'symptoms': self.edit_symptoms.text.strip() or "unknown",
            'findings': self.edit_findings.text.strip() or "unknnown",
            'suggested_diagnosis': self.edit_diagnoses.text.strip() or "unknown",
        }
        self.submit_diagnosis_edit_data(data, diag_id)

    def confirm_deletion_form(self, diag_id):
        confirm_delete_dialog = MDDialog(
            MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
            MDDialogHeadlineText(text="Delete Diagnosis", theme_text_color="Custom", text_color="red"),
            MDDialogContentContainer(
                MDLabel(
                    text = "Deleting a diagnosis is an irreversible process. Are you sure you wish to procede?",
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
                    on_release = lambda *a: self.start_diagnosis_deletion(diag_id)
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

    def submit_diagnosis_edit_data(self, data, diag_id):
        self.show_snack("Please wait as worker is edited")
        Thread(target=self.edit_diagnosis, args=(data, diag_id), daemon=True).start()

    def edit_diagnosis(self, data, diag_id):
        url = f"{SERVER_URL}diagnosis/diagnosis-edit/?hospital_id={self.store.get('hospital')['hsp_id']}&diagnosis_id={diag_id}"
        response = requests.put(url, json=data)
        if response.status_code != 200:
            self.show_snack("Failed to edit diagnosis")
            return
        self.show_snack("Diagnosis edited successfully. You can refresh the page to view them")

    def start_diagnosis_deletion(self, diag_id):
        self.show_snack("Please wait as dignosis is deleted")
        Thread(target=self.delete_diagnosis, args=(diag_id,), daemon=True).start()

    def delete_diagnosis(self, diag_id):
        url = f"{SERVER_URL}diagnosis/diagnosis-delete/?hospital_id={self.store.get('hospital')['hsp_id']}&diagnosis_id={diag_id}"
        response = requests.delete(url)
        if response.status_code != 200:
            self.show_snack("Failed to delete diagnosis")
            return
        self.show_snack("Diagnosis deleted successfully. You can refresh the page to view them")
        
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