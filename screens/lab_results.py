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
import asyncio

from config import SERVER_URL, STORE

from screens.patients import fetch_patients

class ResultsRow(MDListItem):
    patient_name = StringProperty("")
    observations = StringProperty("")
    conclusions = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.obs_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.conc_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="clipboard-check", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.obs_label)
        self.add_widget(self.conc_label)
        
        self.bind(patient_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(observations=lambda inst, val: setattr(self.obs_label, 'text', val))
        self.bind(conclusions=lambda inst, val: setattr(self.conc_label, 'text', val))

class ResultsInfo:
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
            valign="top",       
            size_hint_y=None,   
            markup=True
        )
        lbl.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        return lbl

    def display_results_info(
        self,
        res_data: dict,
    ):
        name_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        name_box.add_widget(MDIcon(icon="account-heart", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        name_box.add_widget(self.make_display_label(f"   Patient: {res_data.get('patient', "Unknown")['patient_name'].upper()}"))

        obs_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        obs_box.add_widget(MDIcon(icon="eye", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        obs_box.add_widget(self.make_display_label(f"   Observations: {res_data.get('observaions', "unknown")}"))
        
        conc_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        conc_box.add_widget(MDIcon(icon="check-decagram", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        conc_box.add_widget(self.make_display_label(text = f"   About: {res_data.get('conclusion', "unknown")}"))
        
        
        date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        date_box.add_widget(self.make_display_label(f"   Added On: {res_data.get('date_added', "YY-MM-DD")}"))
        
        grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
        scroll = MDScrollView()
        scroll.add_widget(grid)
        
        grid.add_widget(Widget(size_hint_y = None, height = dp(10)))
        grid.add_widget(name_box)
        grid.add_widget(obs_box)
        grid.add_widget(conc_box)
        grid.add_widget(date_box)
        
        return scroll

    def fetch_results(self, intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
        Thread(target=self.fetch_and_return_online_results, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

    def fetch_and_return_online_results(self, intent, sort_term, sort_dir, search_term, callback):
        url = ""
        if intent == "search":
            url = f"{SERVER_URL}lab_results/lab_results-search/?hospital_id={self.store.get('hospital')['hsp_id']}&search_term={search_term}"
        elif intent == "all":
            url = f"{SERVER_URL}lab_results/lab_results-fetch/?hospital_id={self.store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
            else:
                data = []
        except Exception:
            data = []

        if callback:
            self.run_on_main_thread(callback, data)

    @mainthread
    def run_on_main_thread(self, callback, data):
        callback(data)

    def results_add_form(self):
        self.new_patient_name = MDTextField(
            MDTextFieldHintText(text = "Patient"),
            MDTextFieldLeadingIcon(icon="account-heart")
        )
        self.new_obs = MDTextField(
            MDTextFieldHintText(text = "Observation"),
            MDTextFieldLeadingIcon(icon="eye")
        )
        self.new_conc = MDTextField(
            MDTextFieldHintText(text = "Conclusion"),
            MDTextFieldLeadingIcon(icon="check-decagram")
        )
        self.new_patient_id = None
        self.new_result_id = None
        
        name_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        name_box.add_widget(self.new_patient_name)
        name_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_patients()
        )
        name_box.add_widget(name_btn)
        
        
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(name_box)
        content.add_widget(self.new_obs)
        content.add_widget(self.new_conc)
        
        self.results_dialog = MDDialog(
            MDDialogIcon(icon = "clipboard-check", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Add Lab Result", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_result_data()
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.results_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.results_dialog.open()
        
    def prepare_result_data(self):
        if not self.new_patient_name.text.strip():
            self.show_snack("Enter patient name")
            return
        if not self.new_obs.text.strip():
            self.show_snack("Enter observations")
            return
        if not self.new_conc.text.strip():
            self.show_snack("Enter conclusions")
            return
        
        data = {
            "patient_id": self.new_patient_id,
            'observations': self.new_obs.text.strip(),
            'conclusion': self.new_conc.text.strip()
        }
        self.submit_result_data(data)
    def submit_result_data(self, data):
        self.show_snack("Please wait as result is added")
        Thread(target=self.add_result, args=(data,), daemon=True).start()

    def add_result(self, data):
        url = f"{SERVER_URL}lab_results/lab_results-add/?hospital_id={self.store.get('hospital')['hsp_id']}"
        response = requests.post(url, json=data)
        if response.status_code != 200:
            self.show_snack("Failed to sync result")
            return
        self.show_snack("Result synced successfully. You can refresh the page to view them")

    def confirm_deletion_form(self, res_id):
        confirm_delete_dialog = MDDialog(
            MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
            MDDialogHeadlineText(text="Delete Result", theme_text_color="Custom", text_color="red"),
            MDDialogContentContainer(
                MDLabel(
                    text = "Deleting a result is an irreversible process. Are you sure you wish to procede?",
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
                    on_release = lambda *a: self.start_result_deletion(res_id)
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

    def start_result_deletion(self, res_id):
        self.show_snack("Please wait as result is deleted")
        Thread(target=self.delete_result, args=(res_id,), daemon=True).start()

    def delete_result(self, res_id):
        url = f"{SERVER_URL}lab_results/lab_results-delete/?hospital_id={self.store.get('hospital')['hsp_id']}&lab_result_id={res_id}"
        response = requests.delete(url)
        if response.status_code != 200:
            self.show_snack("Failed to sync result")
            return
        self.show_snack("Result synced successfully")
        
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
        self.new_patient_name.text = patient
        self.new_patient_id = patient_id
        print(self.new_patient_id)

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
                for p in (self.patients or [])
            ]
    
    def make_text_field(self, field_name, field_icon, field_text=None):
        text_field = MDTextField(
            MDTextFieldHintText(text=field_name),
            MDTextFieldLeadingIcon(icon=field_icon),
            text=str(field_text or "")
        )
        return text_field
    
    def result_edit_form(self, res: dict):
        self.edit_obs = self.make_text_field("Observations", "eye", res.get("observations", None))
        self.edit_conc = self.make_text_field("Conclusion", "check-decagram", res.get("conclusion", None))   

        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(self.edit_obs)
        content.add_widget(self.edit_conc)

        self.result_edit_dialog = MDDialog(
            MDDialogIcon(icon = "clipboard-check", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Edit Lab Result", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_res_data(res)
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.result_edit_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.result_edit_dialog.open()
        

    def prepare_res_data(self, res: dict):
        
        data = {
            "observations": self.edit_obs.text.strip(),
            'conclusion': self.edit_conc.text.strip(),
        }
        self.submit_res_edit_data(data, res.get("result_id"))
    
    def submit_res_edit_data(self, data, res_id):
        self.show_snack("Please wait as result is edited")
        Thread(target=self.edit_res, args=(data, res_id), daemon=True).start()

    def edit_res(self, data, res_id):
        url = f"{SERVER_URL}lab_results/lab_results-edit/?hospital_id={self.store.get('hospital')['hsp_id']}&lab_result_id={res_id}"
        response = requests.put(url, json=data)
        print(data)
        if response.status_code != 200:
            self.show_snack("Failed to sync result")
            return
        self.show_snack("Result synced successfully. You can refresh the page to view them")
