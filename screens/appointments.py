from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivy.clock import mainthread
from kivy.uix.recycleview import RecycleView
from kivy.storage.jsonstore import JsonStore
from kivy.uix.recycleboxlayout import RecycleBoxLayout

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
from kivymd.uix.pickers import MDDockedDatePicker, MDTimePickerDialHorizontal
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from threading import Thread
import requests
from datetime import datetime, timedelta
from config import SERVER_URL
from screens.patients import fetch_patients
from screens.services import fetch_services
from screens.worker import fetch_workers
from config import STORE
from utils import has_internet
import asyncio

class AppointmentsRow(MDListItem):
    patient_name = StringProperty("")
    app_desc = StringProperty("")
    app_date = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.desc_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.date_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="clock", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.desc_label)
        self.add_widget(self.date_label)
        
        self.bind(patient_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(app_desc=lambda inst, val: setattr(self.desc_label, 'text', val))
        self.bind(app_date=lambda inst, val: setattr(self.date_label, 'text', val))

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

class ConsultantsRow(MDListItem):
    worker_name = StringProperty("")
    worker_email = StringProperty("")
    worker_role = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.email_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.role_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="account-circle-outline", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.email_label)
        self.add_widget(self.role_label)
        
        self.bind(worker_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(worker_email=lambda inst, val: setattr(self.email_label, 'text', val))
        self.bind(worker_role=lambda inst, val: setattr(self.role_label, 'text', val))

class AppointmentsInfo:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.patients = {}
        self.consultants = {}
        self.services = {}
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

    def display_appointments_info(
        self,
        app_data: dict,
    ):
        name_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        name_box.add_widget(MDIcon(icon="account-heart", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        name_box.add_widget(self.make_display_label(f"   Patient: {app_data.get('patient', "Unknown")['patient_name'].upper()}"))

        desc_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        desc_box.add_widget(MDIcon(icon="information-outline", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        desc_box.add_widget(self.make_display_label(f"   About: {app_data.get('appointment_desc', "unknown")}"))
        
        date_at_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        date_at_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        date_at_box.add_widget(self.make_display_label(text = f"   Begins On: {app_data.get('date_requested', "YY-MM-DD")}"))
        
        time_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        time_box.add_widget(MDIcon(icon="clock", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        time_box.add_widget(self.make_display_label(text = f"   Starts At: {app_data.get('time_requested', "00:00")}"))
        
        
        date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
        date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
        date_box.add_widget(self.make_display_label(f"   Added On: {app_data.get('date_added', "YY-MM-DD")}"))
        
        grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
        scroll = MDScrollView()
        scroll.add_widget(grid)
        
        grid.add_widget(Widget(size_hint_y = None, height = dp(10)))
        grid.add_widget(name_box)
        grid.add_widget(desc_box)
        grid.add_widget(date_at_box)
        grid.add_widget(time_box)
        grid.add_widget(date_box)
        
        return scroll

    def fetch_apps(self, intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
        Thread(target=self.fetch_and_return_online_apps, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

    def fetch_and_return_online_apps(self, intent, sort_term, sort_dir, search_term, callback):
        url = ""
        hospital_id = self.store.get('hospital', {}).get('hsp_id')
        if not hospital_id:
            if callback:
                self.run_on_main_thread(callback, [])
            return

        if intent == "search":
            url = f"{SERVER_URL}appointments/appointments-search/?hospital_id={hospital_id}&search_term={search_term}"
        elif intent == "all":
            url = f"{SERVER_URL}appointments/appointments-fetch/?hospital_id={hospital_id}&sort_term={sort_term}&sort_dir={sort_dir}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching apps: {e}")
            data = []

        if callback:
            self.run_on_main_thread(callback, data)


    @mainthread
    def run_on_main_thread(self, callback, data):
        callback(data)

    def apps_add_form(self):
        self.new_patient_name = MDTextField(
            MDTextFieldHintText(text = "Patient"),
            MDTextFieldLeadingIcon(icon="account-heart")
        )
        self.new_service = MDTextField(
            MDTextFieldHintText(text = "Service"),
            MDTextFieldLeadingIcon(icon="toolbox")
        )
        self.new_consultant = MDTextField(
            MDTextFieldHintText(text = "Consultant"),
            MDTextFieldLeadingIcon(icon="account-circle-outline")
        )
        self.new_desc = MDTextField(
            MDTextFieldHintText(text = "Findings"),
            MDTextFieldLeadingIcon(icon="information-outline")
        )
        self.new_date_schedule = MDTextField(
            MDTextFieldHintText(text = "Set On"),
            MDTextFieldLeadingIcon(icon="calendar")
        )
        self.new_time_schedule = MDTextField(
            MDTextFieldHintText(text = "Start At"),
            MDTextFieldLeadingIcon(icon="clock")
        )
        self.new_patient_id = None
        self.new_service_id = None
        self.new_consultant_id = None
        
        name_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        name_box.add_widget(self.new_patient_name)
        name_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_patients()
        )
        name_box.add_widget(name_btn)
        
        date_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        date_box.add_widget(self.new_date_schedule)
        date_box.add_widget(MDIconButton(icon="calendar", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: self.show_date_picker(self.new_date_schedule)))
        
        time_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        time_box.add_widget(self.new_time_schedule)
        time_box.add_widget(MDIconButton(icon="clock", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: self.time_dialog()))

        
        service_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        service_box.add_widget(self.new_service)
        service_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_services()
        )
        service_box.add_widget(service_btn)
        
        consultant_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        consultant_box.add_widget(self.new_consultant)
        consultant_btn = MDIconButton(
            icon="chevron-down", theme_icon_color="Custom", 
            icon_color="blue", on_release = lambda *a: self.show_consultants()
        )
        consultant_box.add_widget(consultant_btn)
        
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(name_box)
        content.add_widget(service_box)
        content.add_widget(consultant_box)
        content.add_widget(date_box)
        content.add_widget(time_box)
        
        self.apps_dialog = MDDialog(
            MDDialogIcon(icon = "clock", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Add Appointment", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_apps_data()
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.apps_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.apps_dialog.open()
        
    def prepare_apps_data(self):
        if not self.new_patient_name.text.strip():
            self.show_snack("Enter patient name")
            return
        if not self.new_service.text.strip():
            self.show_snack("Enter service")
            return
        if not self.new_consultant.text.strip():
            self.show_snack("Enter consultant")
            return
        if not self.new_date_schedule.text.strip():
            self.show_snack("Enter schedule date")
            return
        
        if not self.new_time_schedule.text.strip():
            self.show_snack("Enter schedule time")
            return
        
        new_date_scheduled = self.new_date_schedule.text.strip()
        time_string = self.new_time_schedule.text.strip()
        
        if not self.is_valid_date(new_date_scheduled):
            self.show_snack("Invalid date format.")
            return
        if not self.is_valid_time(time_string):
            self.show_snack("Invalid time format.")
            return
        time_scheduled = datetime.strptime(time_string, "%I:%M %p").strftime("%H:%M:%S")

        data = {
            "patient_id": self.new_patient_id,
            "consultant_id": self.new_consultant_id,
            "service_id": self.new_service_id,
            "appointment_desc": self.new_desc.text.strip(),
            "date_scheduled": new_date_scheduled,
            "time_scheduled": time_scheduled,
        }

        print("Data submitted: ", data)
        self.submit_apps_data(data)
    def submit_apps_data(self, data):
        self.show_snack("Please wait as appointment is added")
        Thread(target=self.add_appointment, args=(data,), daemon=True).start()

    def add_appointment(self, data):
        url = f"{SERVER_URL}appointments/appointments-add/?hospital_id={self.store.get('hospital')['hsp_id']}"
        response = requests.post(url, json=data)
        if response.status_code != 200:
            self.show_snack("Failed to sync appointment")
            return
        self.show_snack("Appointment synced to cloud.")

    def make_text_field(self, field_name, field_icon, field_text=None):
        text_field = MDTextField(
            MDTextFieldHintText(text=field_name),
            MDTextFieldLeadingIcon(icon=field_icon),
            text=str(field_text or "")
        )
        return text_field

    def apps_edit_form(self, app: dict):
        self.edit_desc = self.make_text_field("About", "information-outline", app.get("appointment_desc", None))
        self.edit_date = self.make_text_field("Date", "calendar", app.get("date_requested", None))
        self.edit_time = self.make_text_field("Time", "clock", app.get("time_requested", None))   
        
        date_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        date_box.add_widget(self.edit_date)
        date_box.add_widget(MDIconButton(icon="calendar", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: self.show_date_picker(self.edit_date)))
        
        time_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
        time_box.add_widget(self.edit_time)
        time_box.add_widget(MDIconButton(icon="clock", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: self.time_dialog()))
        
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
        content.add_widget(self.edit_desc)
        content.add_widget(date_box)
        content.add_widget(time_box)
        
        self.app_edit_dialog = MDDialog(
            MDDialogIcon(icon = "clock", theme_icon_color="Custom", icon_color="blue"),
            MDDialogHeadlineText(text = "Edit Appointment", bold=True, theme_text_color="Custom", text_color="blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="check", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "blue",
                    on_release = lambda *a: self.prepare_app_edit_data(app.get('appointment_id'))
                ),
                MDIconButton(
                    icon="close", 
                    theme_icon_color="Custom", 
                    icon_color="white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.app_edit_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10),
            ),
            auto_dismiss = False
        )
        self.app_edit_dialog.open()
        

    def prepare_app_edit_data(self, app_id):
        time_string = self.edit_time.text.strip()
        time_scheduled = datetime.strptime(time_string, "%I:%M %p").strftime("%H:%M:%S")
        
        edit_date_scheduled = self.edit_date.text.strip()
        
        if not self.is_valid_date(edit_date_scheduled):
            self.show_snack("Invalid date format.")
            return
        if not self.is_valid_time(time_string):
            self.show_snack("Invalid time format.")
            return
        
        data = {
            'appointment_desc': self.edit_desc.text.strip(),
            'date_scheduled': edit_date_scheduled,
            'time_scheduled': time_scheduled,
        }
        print("appointment edit data: ", data)
        self.submit_app_edit_data(data, app_id)

    def confirm_deletion_form(self, app_id):
        confirm_delete_dialog = MDDialog(
            MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
            MDDialogHeadlineText(text="Delete Appointment", theme_text_color="Custom", text_color="red"),
            MDDialogContentContainer(
                MDLabel(
                    text = "Deleting an appointment is an irreversible process. Are you sure you wish to procede?",
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
                    on_release = lambda *a: self.start_app_deletion(app_id)
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

    def submit_app_edit_data(self, data, app_id):
        self.show_snack("Please wait as appointment is edited")
        Thread(target=self.edit_apps, args=(data, app_id), daemon=True).start()

    def edit_apps(self, data, app_id):
        url = f"{SERVER_URL}appointments/appointments-edit/?hospital_id={self.store.get('hospital')['hsp_id']}&appointment_id={app_id}"
        response = requests.put(url, json=data)
        if response.status_code != 200:
            self.show_snack("Failed to sync appointment")
            return
        self.show_snack("Appointment synced successfully")

    def start_app_deletion(self, app_id):
        self.show_snack("Please wait as appointment is deleted")
        Thread(target=self.delete_app, args=(app_id,), daemon=True).start()

    def delete_app(self, app_id):
        url = f"{SERVER_URL}appointments/appointments-delete/?hospital_id={self.store.get('hospital')['hsp_id']}&appointment_id={app_id}"
        response = requests.delete(url)
        if response.status_code != 200:
            self.show_snack("Failed to sync appointment")
            return
        self.show_snack("Appointment synced successfully")

    def show_date_picker(self, target_field):
        day = month = year = "00"
        
        def on_select_day(instance, value):
            nonlocal day
            day = f"{int(value):02}" if value else "00"

        def on_select_month(instance, value):
            nonlocal month
            month = f"{int(value):02}" if value else "00"

        def on_select_year(instance, value):
            nonlocal year
            year = str(value) if value else "0000"

        def create_date(*args):
            date = f"{year}-{month}-{day}"
            target_field.text = date
            date_dialog.dismiss()

        def close_date_dialog(*args):
            date_dialog.dismiss()

        date_dialog = MDDockedDatePicker()
        date_dialog.pos_hint = {"center_x": .5, "center_y": .5}
        date_dialog.bind(
            on_select_day=on_select_day,
            on_select_month=on_select_month,
            on_select_year=on_select_year,
            on_ok=create_date,
            on_cancel=close_date_dialog
        )
        date_dialog.open()
    
    def time_dialog(self):
        self.hour = 0
        self.minute = 0
        self.am_pm = ""
        self.time_form = MDTimePickerDialHorizontal()
        self.time_form.open()
        self.time_form.bind(
            on_selector_hour = self.show_hour,
            on_selector_minute = self.show_minute,
            on_am_pm = self.show_am_pm,
            on_cancel = self.close_time_dialog,
            on_ok = self.create_time
        )
    
    def show_hour(self, instance, value):
        self.hour = value
    def show_minute(self, instance, value):
        self.minute = value
    def show_am_pm(self, instance, value):
        self.am_pm = value
    
    def create_time(self, *args):
        time = f"{self.hour}:{self.minute} {self.am_pm.upper()}"
        if hasattr(self, "new_time_schedule"):
            self.new_time_schedule.text = time
        elif hasattr(self, "edit_time"):
            self.edit_time.text = time
        else:
            return
        self.time_form.dismiss()
    
    def close_time_dialog(self, *args):
        self.time_form.dismiss()
    
    def is_valid_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def is_valid_time(self, time_str):
        try:
            datetime.strptime(time_str, "%I:%M %p")
            return True
        except ValueError:
            return False
    
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
    
    @mainthread
    def make_services_container(self):
        if not self.services:
            self.show_snack("No services found")
            return

        prvb = RecycleBoxLayout(
            default_size=(None, dp(100)),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(5),
            orientation="vertical"
        )
        prvb.bind(minimum_height=prvb.setter("height")) 

        self.services_prev = RecycleView(
            scroll_type=['bars', 'content'],
            bar_width=0,
            size_hint=(1, None),
            height=dp(300),
        )
        self.services_prev.add_widget(prvb)
        self.services_prev.layout_manager = prvb 
        self.services_prev.viewclass = "ServicesRow"

        data = []
        for service in self.services:
            service = service or {}  
            data.append({
                'service_name': (service.get('service_name') or "Unknown").strip(),
                'service_desc': (service.get('service_desc') or "Unknown").strip(),
                'service_price': str(service.get('service_price', 0.0)),
                'show_profile': lambda x=service.get('service_name'), y=service.get('service_id'): self.display_service(x, y)
            })

        self.services_prev.data = data
        self.services_display_form(self.services_prev)

    def services_display_form(self, container):
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10), padding = dp(5))
        self.services_search_field = MDTextField(
            MDTextFieldHintText(text="search..."),
            mode = "filled"
        )
        self.services_search_field.bind(text=lambda instance, value: self.search_services("search"))
        content.add_widget(self.services_search_field)
        content.add_widget(container)
        
        self.services_display_dialog = MDDialog(
            MDDialogIcon(icon="magnify", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Select Service", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.services_display_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            size_hint_y = None,
            height = dp(300)
        )
        self.services_display_dialog.open()
        self.services_display_dialog.auto_dismiss = False
        
    def display_service(self, service, service_id):
        self.services_display_dialog.dismiss()
        self.new_service.text = service
        self.new_service_id = service_id
    
    @mainthread
    def make_consultants_container(self):
        if not self.consultants:
            self.show_snack("No consultants found")
            return

        prvb = RecycleBoxLayout(
            default_size=(None, dp(100)),
            default_size_hint=(1, None),
            size_hint_y=None,
            spacing=dp(5),
            orientation="vertical"
        )
        prvb.bind(minimum_height=prvb.setter("height")) 

        self.consultants_prev = RecycleView(
            scroll_type=['bars', 'content'],
            bar_width=0,
            size_hint=(1, None),
            height=dp(300),
        )
        self.consultants_prev.add_widget(prvb)
        self.consultants_prev.layout_manager = prvb 
        self.consultants_prev.viewclass = "ConsultantsRow"

        data = []
        for c in self.consultants:
            c = c or {} 
            data.append({
                'worker_name': (c.get('worker_name') or "Unknown").strip(),
                'worker_email': (c.get('worker_email') or "unknown").lower(),
                'worker_role': (c.get('worker_role') or "Unknown").strip(),
                'show_profile': lambda x=c.get('worker_name'), y=c.get('worker_id'): self.display_consultants(x, y)
            })

        self.consultants_prev.data = data
        self.consultants_display_form(self.consultants_prev)

    def consultants_display_form(self, container):
        content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10), padding = dp(5))
        self.consultants_search_field = MDTextField(
            MDTextFieldHintText(text="search..."),
            mode = "filled"
        )
        self.consultants_search_field.bind(text=lambda instance, value: self.search_workers("search"))
        content.add_widget(self.consultants_search_field)
        content.add_widget(container)
        
        self.consultants_display_dialog = MDDialog(
            MDDialogIcon(icon="magnify", theme_icon_color = "Custom", icon_color = "blue"),
            MDDialogHeadlineText(text = "Select Consultants", theme_text_color = "Custom", text_color = "blue"),
            content,
            MDDialogButtonContainer(
                Widget(),
                MDIconButton(
                    icon="close",
                    theme_icon_color = "Custom",
                    icon_color = "white",
                    theme_bg_color = "Custom",
                    md_bg_color = "red",
                    on_release = lambda *a: self.consultants_display_dialog.dismiss()
                ),
                spacing = dp(10),
                padding = dp(10)
            ),
            size_hint_y = None,
            height = dp(300)
        )
        self.consultants_display_dialog.open()
        self.consultants_display_dialog.auto_dismiss = False
        
    def display_consultants(self, consultant, worker_id):
        self.consultants_display_dialog.dismiss()
        self.new_consultant.text = consultant
        self.new_consultant_id = worker_id
    

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
    
    
    def show_services(self):
        def on_services_fetched(services):
            if not services:
                return
            self.services = services
            self.make_services_container()
        
        fetch_services("all", "all", "desc", callback=on_services_fetched)
        

    
    def search_services(self, *args):
        term = self.services_search_field.text.strip()

        def on_services_fetched(services):
            if not services:
                print("Services not found")
                return
            self.services = services
            self.update_service_rv()

        if not term:
            self.show_snack("Enter something to search")
            fetch_services("all", "all", "desc", callback=on_services_fetched)
            return
        
        fetch_services(
            intent="search",
            search_term=term,
            callback=on_services_fetched
        )
    
    @mainthread
    def update_service_rv(self):
        if hasattr(self, "services_prev"):
            self.services_prev.data = [
                {
                    'service_name': s['service_name'] or "unknown",
                    'service_desc': s['service_desc'] or "unknown",
                    'service_price': str(s['service_price']) or "0.0",
                    'show_profile': lambda x=s['service_name'], y=s['service_id']: self.display_service(x, y)
                }
                for s in (self.services or [])
            ]
    
    def show_consultants(self):
        def on_workers_fetched(workers):
            if not workers:
                return
            self.consultants = workers
            self.make_consultants_container()
        
        fetch_workers("all", "all", "desc", callback=on_workers_fetched)
        

    
    def search_workers(self, *args):
        term = self.consultants_search_field.text.strip()

        def on_workers_fetched(workers):
            if not workers:
                return
            self.consultants = workers
            self.update_consultant_rv()

        if not term:
            self.show_snack("Enter something to search")
            fetch_workers("all", "all", "desc", callback=on_workers_fetched)
            return
        
        fetch_workers(
            intent="search",
            search_term=term,
            callback=on_workers_fetched
        )
    
    @mainthread
    def update_consultant_rv(self):
        if hasattr(self, "consultants_prev"):
            self.consultants_prev.data = [
                {
                    'worker_name': c['worker_name'] or "unknown",
                    'worker_eamil': c['worker_email'] or "example@email.com",
                    'worker_role': c['worker_role'] or "unknown",
                    'show_profile': lambda x=c['worker_name'], y=c['worker_id']: self.display_consultants(x, y)
                }
                for c in (self.consultants or [])
            ]