from kivy.lang import Builder
from kivy.metrics import dp, sp

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from screens.patients import (
    fetch_patients,
    patients_edit_form,
    patients_add_form,
    display_patients_info,
    confirm_deletion_form
)
from screens.appointments import AppointmentsInfo
from config import resource_path


Builder.load_file(resource_path("screens/reception.kv"))

class ReceptionScreen(MDScreen):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ids.search_field.bind(text=self._on_search_field_text)

    def _on_search_field_text(self, instance, value):
        if self.current_search_callback:
            self.current_search_callback(value)
    
    def display_items(self, prev_class, items, flag, mapper):
        prev = self.ids.rec_view
        self.ids.rec_box.default_size = (None, dp(80))
        prev.viewclass = prev_class

        data = [mapper(i) for i in items]
        prev.data = data
    
    def patients_mapper(self, pat: dict | None):
        pat = pat or {}

        return {
            'patient_name': (pat.get("patient_name") or "Unknown").strip(),
            'patient_email': (pat.get("patient_email") or "example@gmail.com").strip(),
            'patient_phone': (pat.get("patient_phone") or "0712345678").strip(),
            'show_profile': lambda pat_data=pat: self.display_patients(pat_data)
        }


    def show_patients(self):
        self.current_search_callback = self.search_patients
        self.ids.add_btn.on_release = lambda *a: patients_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_pat_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_patients_fetched(patients):
            if not patients:
                self.show_snack("Patients not found")
                return
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
                    on_release = lambda *a: confirm_deletion_form(pat_data.get("patient_id"))
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
            'app_date': str(app.get("date_requested") or "YY-MM-DD").strip(),
            'show_profile': lambda app_data=app: self.display_appointments(app_data)
        }


    def show_appointments(self):
        self.current_search_callback = self.search_appointments

        self.ids.add_btn.on_release = lambda *a: AppointmentsInfo().apps_add_form()
        self.ids.sort_btn.on_release = lambda *a: self.show_apps_sort_dropdown(self.ids.sort_btn)
        self.ids.rec_box.clear_widgets()
        def on_apps_fetched(apps):
            if not apps:
                self.show_snack("Appointments not found")
                return
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
    
    def preview_display(self, container, prev_header):
        self.ids.disp_view.clear_widgets()
        self.ids.disp_view.add_widget(prev_header)
        self.ids.disp_view.add_widget(container)
    
    
    def show_snack(self, text):
        MDSnackbar(
            MDSnackbarText(text=text), 
            pos_hint={'center_x': 0.5}, 
            size_hint_x=0.5, 
            orientation='horizontal'
        ).open()