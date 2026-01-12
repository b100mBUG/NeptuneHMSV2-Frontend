from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivy.clock import mainthread
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

store = STORE

def display_patients_info(pat_data: dict):

    patient_name = (pat_data.get("patient_name") or "Unknown").upper()
    patient_email = pat_data.get("patient_email", "example@gmail.com")
    patient_phone = pat_data.get("patient_phone", "0712345678")
    patient_id = pat_data.get("patient_id_no", "123456778")
    patient_gender = pat_data.get("patient_gender", "unknown")
    patient_address = pat_data.get("patient_address", "unknown")
    patient_dob = pat_data.get("patient_dob", "YY-MM-DD")

    patient_weight = pat_data.get("patient_weight", "unknown")
    patient_avg_pulse = pat_data.get("patient_avg_pulse", "unknown")
    patient_bp = pat_data.get("patient_bp", "unknown")
    patient_chronic = pat_data.get("patient_chronic_condition", "unknown")
    patient_allergy = pat_data.get("patient_allergy", "unknown")
    patient_blood = pat_data.get("patient_blood_type", "unknown")
    date_added = pat_data.get("date_added", "YY-MM-DD")

    bio_head = MDLabel(
        text="BIO INFO",
        theme_text_color="Custom",
        text_color="blue",
        halign="center",
    )

    medic_head = MDLabel(
        text="MEDICAL INFO",
        theme_text_color="Custom",
        text_color="blue",
        halign="center",
    )

    name_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    name_box.add_widget(MDIcon(icon="account-heart", theme_icon_color="Custom", icon_color="blue"))
    name_box.add_widget(make_display_label(f"Patient: {patient_name}"))

    email_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    email_box.add_widget(MDIcon(icon="gmail", theme_icon_color="Custom", icon_color="blue"))
    email_box.add_widget(make_display_label(f"Email: {patient_email}"))

    phone_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    phone_box.add_widget(MDIcon(icon="phone", theme_icon_color="Custom", icon_color="blue"))
    phone_box.add_widget(make_display_label(f"Contact: {patient_phone}"))

    id_no_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    id_no_box.add_widget(MDIcon(icon="card-account-details", theme_icon_color="Custom", icon_color="blue"))
    id_no_box.add_widget(make_display_label(f"National ID: {patient_id}"))

    gender_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    gender_box.add_widget(MDIcon(icon="gender-male-female", theme_icon_color="Custom", icon_color="blue"))
    gender_box.add_widget(make_display_label(f"Gender: {patient_gender}"))

    address_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    address_box.add_widget(MDIcon(icon="map-marker", theme_icon_color="Custom", icon_color="blue"))
    address_box.add_widget(make_display_label(f"Address: {patient_address}"))

    dob_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    dob_box.add_widget(MDIcon(icon="calendar-heart", theme_icon_color="Custom", icon_color="blue"))
    dob_box.add_widget(make_display_label(f"Born On: {patient_dob}"))

    weight_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    weight_box.add_widget(MDIcon(icon="weight-kilogram", theme_icon_color="Custom", icon_color="blue"))
    weight_box.add_widget(make_display_label(f"Weight: {patient_weight} KG"))

    avg_pulse_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    avg_pulse_box.add_widget(MDIcon(icon="heart-pulse", theme_icon_color="Custom", icon_color="blue"))
    avg_pulse_box.add_widget(make_display_label(f"Avg. Pulse: {patient_avg_pulse} BpM"))

    bp_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    bp_box.add_widget(MDIcon(icon="gauge", theme_icon_color="Custom", icon_color="blue"))
    bp_box.add_widget(make_display_label(f"Blood Pressure: {patient_bp} mmHg"))

    chronic_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    chronic_box.add_widget(MDIcon(icon="medical-bag", theme_icon_color="Custom", icon_color="blue"))
    chronic_box.add_widget(make_display_label(f"Chronics: {patient_chronic}"))

    allergy_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    allergy_box.add_widget(MDIcon(icon="allergy", theme_icon_color="Custom", icon_color="blue"))
    allergy_box.add_widget(make_display_label(f"Allergies: {patient_allergy}"))

    blood_type_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    blood_type_box.add_widget(MDIcon(icon="blood-bag", theme_icon_color="Custom", icon_color="blue"))
    blood_type_box.add_widget(make_display_label(f"Blood Type: {patient_blood}"))

    date_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    date_box.add_widget(MDIcon(icon="calendar", theme_icon_color="Custom", icon_color="blue"))
    date_box.add_widget(make_display_label(f"Added On: {date_added}"))

    grid = MDGridLayout(
        cols=1,
        padding=dp(10),
        spacing=dp(10),
        adaptive_height=True,
    )

    scroll = MDScrollView()
    scroll.add_widget(grid)

    grid.add_widget(Widget(size_hint_y=None, height=dp(10)))
    grid.add_widget(bio_head)
    grid.add_widget(Widget(size_hint_y=None, height=dp(10)))
    grid.add_widget(name_box)
    grid.add_widget(email_box)
    grid.add_widget(phone_box)
    grid.add_widget(id_no_box)
    grid.add_widget(gender_box)
    grid.add_widget(address_box)
    grid.add_widget(dob_box)

    grid.add_widget(MDDivider())
    grid.add_widget(Widget(size_hint_y=None, height=dp(10)))
    grid.add_widget(medic_head)
    grid.add_widget(Widget(size_hint_y=None, height=dp(10)))

    grid.add_widget(weight_box)
    grid.add_widget(avg_pulse_box)
    grid.add_widget(bp_box)
    grid.add_widget(chronic_box)
    grid.add_widget(allergy_box)
    grid.add_widget(blood_type_box)
    grid.add_widget(date_box)

    return scroll


def fetch_patients(intent="all", sort_term="all", sort_dir="desc", search_term="ss", search_by="ss", callback=None):
    Thread(target=fetch_and_return_online_patients, args=(intent, sort_term, sort_dir, search_term, search_by, callback), daemon=True).start()

def fetch_and_return_online_patients(intent, sort_term, sort_dir, search_term, search_by, callback):
    url = ""
    if intent == "search":
        url = f"{SERVER_URL}patients/patients-search/?hospital_id={store.get('hospital')['hsp_id']}&search_by={search_by}&search_term={search_term}"
    elif intent == "all":
        url = f"{SERVER_URL}patients/patients-fetch/?hospital_id={store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"    

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


@mainthread
def run_on_main_thread(callback, data):
    callback(data)

def patients_add_form():
    patient_name = MDTextField(
        MDTextFieldHintText(text = "Patient"),
        MDTextFieldLeadingIcon(icon="account-heart")
    )
    patient_gender = MDTextField(
        MDTextFieldHintText(text = "Gender"),
        MDTextFieldLeadingIcon(icon="gender-male-female")
    )
    patient_dob = MDTextField(
        MDTextFieldHintText(text = "D.O.B"),
        MDTextFieldLeadingIcon(icon="calendar-heart")
    )
    
    gender_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    gender_box.add_widget(patient_gender)
    gender_btn = MDIconButton(icon="chevron-down", theme_icon_color="Custom", icon_color="blue", on_release = lambda *a: show_dropdown(gender_btn, patient_gender, ["Male", "Female"], fill_gender_field))
    gender_box.add_widget(gender_btn)
    
    dob_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    dob_box.add_widget(patient_dob)
    dob_box.add_widget(MDIconButton(icon="calendar", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: show_date_picker(patient_dob)))

    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(patient_name)
    content.add_widget(gender_box)
    content.add_widget(dob_box)
    add_btn = MDIconButton(
        icon="check", 
        theme_icon_color="Custom", 
        icon_color="white",
        theme_bg_color = "Custom",
        md_bg_color = "blue",
        on_release = lambda *a: prepare_patient_data(add_btn)
    )
    patient_dialog = MDDialog(
        MDDialogIcon(icon = "account-heart", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Add Patient", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            add_btn,
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: patient_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    patient_dialog.open()
    
    def prepare_patient_data(add_btn):
        if not patient_name.text.strip():
            show_snack("Enter patient name")
            return
        if not patient_gender.text.strip():
            show_snack("Enter patient gender")
            return
        if not patient_dob.text.strip():
            show_snack("Enter patient d.o.b")
            return
        if not is_valid_date(patient_dob.text.strip()):
            show_snack("Invalid date passed")
            return
        pat_dob = ""
        try:
            pat_dob = datetime.strptime(patient_dob.text.strip(), "%Y-%m-%d")
        except Exception:
            show_snack("Invalid date passed.")
        
        data = {
            "patient_name": patient_name.text.strip(),
            'patient_gender': patient_gender.text.strip(),
            'patient_dob': pat_dob.strftime("%Y-%m-%d")
        }
        add_btn.disabled = True
        submit_patient_data(data, add_btn)
def submit_patient_data(data, add_btn):
    show_snack("Please wait as patient is added")
    Thread(target=add_patient, args=(data,add_btn), daemon=True).start()

def add_patient(data, add_btn):
    url = f"{SERVER_URL}patients/patients-add/?hospital_id={store.get('hospital')['hsp_id']}"
    response = requests.post(url, json=data)
    if response.status_code != 200:
        add_btn.disabled = False
        show_snack("Failed to sync patient")
        return
    add_btn.disabled = False
    show_snack("Patient synced successfully.")

def make_text_field(field_name, field_icon, field_text=None):
    text_field = MDTextField(
        MDTextFieldHintText(text=field_name),
        MDTextFieldLeadingIcon(icon=field_icon),
        text=str(field_text or "")
    )
    return text_field

def patients_edit_form(pat: dict):
    patient_name = make_text_field("Patient", "account-heart", pat.get("patient_name", None))
    patient_gender = make_text_field("Gender", "gender-male-female", pat.get("patient_gender", None))
    patient_dob = make_text_field("D.O.B", "calendar-heart", pat.get("patient_dob", None))
    patient_id_no = make_text_field("I.D NO", "account-heart", pat.get("patient_id_no", None))
    patient_email = make_text_field("Email", "gmail", pat.get("patient_email", None))
    patient_phone = make_text_field("Phone", "phone", pat.get("patient_phone", None))
    patient_address = make_text_field("Address", "map-marker", pat.get("patient_address", None))
    patient_weight = make_text_field("Weight", "weight-kilogram", pat.get("patient_weight", None))
    patient_avg_pulse = make_text_field("Avg Pulse", "heart-pulse", pat.get("patient_avg_pulse", None))
    patient_bp = make_text_field("Blood Pressure", "gauge", pat.get("patient_bp", None))
    patient_blood_type = make_text_field("Blood Type", "blood-bag", pat.get("patient_blood_type", None))
    patient_allergy = make_text_field("Allergy", "allergy", pat.get("patient_allergy", None))
    patient_chronic = make_text_field("Chronic Condition", "allergy", pat.get("patient_chronic_condition", None))
    
    
    gender_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    gender_box.add_widget(patient_gender)
    gender_btn = MDIconButton(icon="chevron-down", theme_icon_color="Custom", icon_color="blue", on_release = lambda *a: show_dropdown(gender_btn, patient_gender, ["Male", "Female"], fill_gender_field))
    gender_box.add_widget(gender_btn)
    
    dob_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    dob_box.add_widget(patient_dob)
    dob_box.add_widget(MDIconButton(icon="calendar", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: show_date_picker(patient_dob)))
    
    bld_typ_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    bld_typ_box.add_widget(patient_blood_type)
    bld_typ_btn = MDIconButton(icon="chevron-down", theme_icon_color="Custom", icon_color="blue", on_release = lambda *a: show_dropdown(bld_typ_btn, patient_blood_type, [
        "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-" 
    ], fill_bld_typ_field))
    bld_typ_box.add_widget(bld_typ_btn)

    grid = MDGridLayout(cols=1, size_hint_y = None, adaptive_height=True, spacing = dp(10), padding = dp(5))
    scroll = MDScrollView(size_hint_y = None, height = dp(450))
    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    grid.add_widget(patient_name)
    grid.add_widget(gender_box)
    grid.add_widget(dob_box)
    grid.add_widget(patient_id_no)
    grid.add_widget(patient_email)
    grid.add_widget(patient_address)
    grid.add_widget(patient_weight)
    grid.add_widget(patient_avg_pulse)
    grid.add_widget(patient_bp)
    grid.add_widget(patient_allergy)
    grid.add_widget(patient_chronic)
    grid.add_widget(bld_typ_box)
    scroll.add_widget(grid)
    content.add_widget(scroll)
    
    
    patient_edit_dialog = MDDialog(
        MDDialogIcon(icon = "account-heart", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Edit Patient", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_patient_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: patient_edit_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    patient_edit_dialog.open()
    

    def prepare_patient_data():
        pat_dob = ""
        try:
            pat_dob = datetime.strptime(patient_dob.text.strip(), "%Y-%m-%d")
        except Exception:
            show_snack("Invalid date passed")
        if patient_email.text.strip():
            if not "@" in patient_email.text.strip():
                show_snack("Enter valid email address or leave field empty")
                return
        
        data = {
            "patient_name": patient_name.text.strip(),
            "patient_gender": patient_gender.text.strip(),
            "patient_dob": patient_dob.text.strip(),  
            'patient_id_number': patient_id_no.text.strip(),
            'patient_email': patient_email.text.strip() if patient_email.text.strip() else "example@gmail.com",
            'patient_phone': patient_phone.text.strip(),
            'patient_address': patient_address.text.strip(),
            'patient_weight': float(patient_weight.text.strip()) if patient_weight.text.strip() else None,
            'patient_avg_pulse': float(patient_avg_pulse.text.strip()) if patient_avg_pulse.text.strip() else None,
            'patient_bp': float(patient_bp.text.strip()) if patient_bp.text.strip() else None,
            'patient_allergy': patient_allergy.text.strip(),
            'patient_blood_type': patient_blood_type.text.strip(),
            'patient_chronic_condition': patient_chronic.text.strip(),
        }
        print("Patient data before submission: ", data)
        submit_patient_edit_data(data, pat.get("patient_id"))

def confirm_deletion_form(pat_id):
    confirm_delete_dialog = MDDialog(
        MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
        MDDialogHeadlineText(text="Delete Patient", theme_text_color="Custom", text_color="red"),
        MDDialogContentContainer(
            MDLabel(
                text = "Deleting a patient is an irreversible process. Are you sure you wish to procede?",
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
                on_release = lambda *a: start_patient_deletion(pat_id)
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

def submit_patient_edit_data(data, pat_id):
    show_snack("Please wait as patient is edited")
    Thread(target=edit_patient, args=(data, pat_id), daemon=True).start()


def edit_patient(data, pat_id):
    url = f"{SERVER_URL}patients/patients-edit/?hospital_id={store.get('hospital')['hsp_id']}&patient_id={pat_id}"
    response = requests.put(url, json=data)
    if response.status_code != 200:
        show_snack("Failed to sync patient")
        return
    show_snack("Patient synced successfully.")

def start_patient_deletion(pat_id):
    show_snack("Please wait as patient is deleted")
    Thread(target=delete_patient, args=(pat_id,), daemon=True).start()

def delete_patient(pat_id):
    url = f"{SERVER_URL}patients/patients-delete/?hospital_id={store.get('hospital')['hsp_id']}&patient_id={pat_id}"
    response = requests.delete(url)
    if response.status_code != 200:
        show_snack("Failed to sync patient")
        return
    show_snack("Patient synced successfully.")

def show_date_picker(target_field):
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

def show_dropdown(caller, target_field, items, func):
    drop_down_items = [
        {
            "text": item,
            "theme_text_color": "Custom",
            "text_color": "blue",
            "bold": True,
            "on_release": lambda item = item: func(item, target_field, menu)
        } for item in items
    ]

    menu = MDDropdownMenu(
        caller=caller,
        items=drop_down_items,
        width_mult=4
    )
    menu.open()

def fill_gender_field(val, target_field, menu):
    target_field.text = val
    menu.dismiss()

def fill_bld_typ_field(val, target_field, menu):
    target_field.text = val
    menu.dismiss()

@mainthread
def show_snack(text):
    MDSnackbar(
        MDSnackbarText(text=text), 
        pos_hint={'center_x': 0.5}, 
        size_hint_x=0.5, 
        orientation='horizontal'
    ).open()
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False