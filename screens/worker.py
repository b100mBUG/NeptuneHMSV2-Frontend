from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp, sp
from kivy.clock import mainthread, Clock
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
from kivymd.uix.selectioncontrol import MDCheckbox

from threading import Thread
import requests
from datetime import datetime, timedelta
import asyncio

from config import SERVER_URL, STORE

class WorkersRow(MDListItem):
    worker_name = StringProperty("")
    worker_email = StringProperty("")
    worker_phone = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.email_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.phone_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="account-circle-outline", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.email_label)
        self.add_widget(self.phone_label)
        
        self.bind(worker_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(worker_email=lambda inst, val: setattr(self.email_label, 'text', val))
        self.bind(worker_phone=lambda inst, val: setattr(self.phone_label, 'text', val))

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

def display_workers_info(wrk_data: dict):
    worker_name = (wrk_data.get("worker_name") or "Unknown").upper()
    worker_email = wrk_data.get("worker_email", "example@gmail.com")
    worker_phone = wrk_data.get("worker_phone", "0712345678")
    worker_role = wrk_data.get("worker_role", "Staff")
    date_added = wrk_data.get("date_added", "YY-MM-DD")

    name_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    name_box.add_widget(MDIcon(icon="account-circle-outline", theme_icon_color="Custom", icon_color="blue"))
    name_box.add_widget(make_display_label(f"Worker: {worker_name}"))

    email_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    email_box.add_widget(MDIcon(icon="gmail", theme_icon_color="Custom", icon_color="blue"))
    email_box.add_widget(make_display_label(f"Email: {worker_email}"))

    phone_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    phone_box.add_widget(MDIcon(icon="phone", theme_icon_color="Custom", icon_color="blue"))
    phone_box.add_widget(make_display_label(f"Contact: {worker_phone}"))

    role_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    role_box.add_widget(MDIcon(icon="account-tie", theme_icon_color="Custom", icon_color="blue"))
    role_box.add_widget(make_display_label(f"Role: {worker_role}"))

    date_box = MDBoxLayout(spacing=dp(5), size_hint_y=None, height=dp(40))
    date_box.add_widget(MDIcon(icon="calendar", theme_icon_color="Custom", icon_color="blue"))
    date_box.add_widget(make_display_label(f"Added On: {date_added}"))

    grid = MDGridLayout(
        cols=1,
        padding=dp(10),
        spacing=dp(10),
        adaptive_height=True
    )

    scroll = MDScrollView()
    scroll.add_widget(grid)

    grid.add_widget(Widget(size_hint_y=None, height=dp(10)))
    grid.add_widget(name_box)
    grid.add_widget(email_box)
    grid.add_widget(phone_box)
    grid.add_widget(role_box)
    grid.add_widget(date_box)

    return scroll


def fetch_workers(intent="all", sort_term="all", sort_dir="desc", search_term="ss", search_by="name", callback=None):
    Thread(target=fetch_and_return_online_workers, args=(intent, sort_term, sort_dir, search_term, search_by, callback), daemon=True).start()

def fetch_and_return_online_workers(intent, sort_term, sort_dir, search_term, search_by, callback):
    url = ""
    if intent == "search":
        url = f"{SERVER_URL}workers/workers-search/?hospital_id={store.get('hospital')['hsp_id']}&search_by={search_by}&search_term={search_term}"
    elif intent == "all":
        url = f"{SERVER_URL}workers/workers-fetch/?hospital_id={store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

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

def workers_add_form():
    worker_name = MDTextField(
        MDTextFieldHintText(text = "Worker"),
        MDTextFieldLeadingIcon(icon="account-circle-outline")
    )
    worker_role = MDTextField(
        MDTextFieldHintText(text = "Role"),
        MDTextFieldLeadingIcon(icon="account-cog")
    )
    
    role_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    role_box.add_widget(worker_role)
    role_btn = MDIconButton(icon="chevron-down", theme_icon_color="Custom", icon_color="blue", on_release = lambda *a: show_dropdown(role_btn, worker_role, [
        "Doctor", "Pharmacist", "Lab Tech", "Receptionist", "Admin"
    ], fill_role_field))
    role_box.add_widget(role_btn)
    
    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(worker_name)
    content.add_widget(role_box)
    
    worker_dialog = MDDialog(
        MDDialogIcon(icon = "account-circle-outline", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Add Worker", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_worker_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: worker_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    worker_dialog.open()
    
    def prepare_worker_data():
        if not worker_name.text.strip():
            show_snack("Enter worker name")
            return
        if not worker_role.text.strip():
            show_snack("Enter worker gender")
            return
        
        data = {
            "worker_name": worker_name.text.strip(),
            'worker_role': worker_role.text.strip(),
        }
        submit_worker_data(data)
def submit_worker_data(data):
    show_snack("Please wait as worker is added")
    Thread(target=add_worker, args=(data,), daemon=True).start()

def add_worker(data):
    url = f"{SERVER_URL}workers/workers-add/?hospital_id={store.get('hospital')['hsp_id']}"
    response = requests.post(url, json=data)
    if response.status_code != 200:
        show_snack("Failed to sync worker")
        return
    show_snack("Worker synced successfully")

def make_text_field(field_name, field_icon, field_text=None):
    text_field = MDTextField(
        MDTextFieldHintText(text=field_name),
        MDTextFieldLeadingIcon(icon=field_icon),
        text=str(field_text or "")
    )
    return text_field

def worker_edit_form(wrk: dict):
    worker_name = make_text_field("Worker", "account-circle-outline", wrk.get("worker_name", None))
    worker_role = make_text_field("Role", "account-cog", wrk.get("worker_role", None))
    worker_email = make_text_field("Email", "gmail", wrk.get("worker_email", None))
    worker_phone = make_text_field("Phone", "phone", wrk.get("worker_phone", None))   
    
    role_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    role_box.add_widget(worker_role)
    role_btn = MDIconButton(icon="chevron-down", theme_icon_color="Custom", icon_color="blue", on_release = lambda *a: show_dropdown(role_btn, worker_role, [
        "Doctor", "Pharmacist", "Lab Tech", "Receptionist", "Admin"
    ], fill_role_field))
    role_box.add_widget(role_btn)

    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(worker_name)
    content.add_widget(role_box)
    content.add_widget(worker_email)
    content.add_widget(worker_phone)
    
    worker_edit_dialog = MDDialog(
        MDDialogIcon(icon = "account-circle-outline", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Edit Workert", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            MDIconButton(
                icon="key", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: worker_pwd_change_form(wrk.get("worker_id"))
            ),
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_worker_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: worker_edit_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    worker_edit_dialog.open()
    

    def prepare_worker_data():
        
        data = {
            'worker_name': worker_name.text.strip() or "unknown",
            'worker_role': worker_role.text.strip() or "user_role",
            'worker_email': worker_email.text.strip() or "example@gmail.com",
            'worker_phone': worker_phone.text.strip() or "0737841451",
        }
        submit_worker_edit_data(data, wrk.get("worker_id"))

def make_pwd_text_field(name, icon):
    return MDTextField(
        MDTextFieldHintText(
            text = name
        ),
        MDTextFieldLeadingIcon(
            icon = icon
        ),
        password = True
    )

def worker_pwd_change_form(wrk_id):
    former_password = make_pwd_text_field("Current Password", "key")
    new_password = make_pwd_text_field("New Password", "key")
    
    check = MDCheckbox(
        size_hint = (None, None),
        size = (dp(40), dp(40)),
        size_hint_x = 0.1,
        pos_hint = {"center_y": .5},
        on_active =  lambda *a: toggle_show_wrk_pass(check.active, former_password, new_password)
    )
    
    worker_pwd_change_dialog = MDDialog(
        MDDialogIcon(icon="key", theme_icon_color = "Custom", icon_color = "blue"),
        MDDialogHeadlineText(text = "Change worker password", theme_text_color = "Custom", text_color = "blue"),
        MDDialogContentContainer(
            former_password,
            new_password,
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
            ),
            spacing = dp(10),
            padding = dp(10),
            orientation = "vertical"
        ),
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_wrk_password(wrk_id)
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: worker_pwd_change_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    worker_pwd_change_dialog.open()
    
    def prepare_wrk_password(wrk_id):
        data = {
            "former_password": former_password.text.strip(),
            "new_password": new_password.text.strip()
        }
        submit_worker_password_data(data, wrk_id)

def toggle_show_wrk_pass(value, former_password, new_password):
    if value:
        former_password.password = False
        new_password.password = False
    else:
        former_password.password = True
        new_password.password = True

def confirm_deletion_form(wrk_id):
    confirm_delete_dialog = MDDialog(
        MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
        MDDialogHeadlineText(text="Delete Worker", theme_text_color="Custom", text_color="red"),
        MDDialogContentContainer(
            MDLabel(
                text = "Deleting a worker is an irreversible process. Are you sure you wish to procede?",
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
                on_release = lambda *a: start_worker_deletion(wrk_id)
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

def submit_worker_edit_data(data, wrk_id):
    show_snack("Please wait as worker is edited")
    Thread(target=edit_worker, args=(data, wrk_id), daemon=True).start()

def edit_worker(data, wrk_id):
    url = f"{SERVER_URL}workers/workers-edit/?hospital_id={store.get('hospital')['hsp_id']}&worker_id={wrk_id}"
    response = requests.put(url, json=data)
    if response.status_code != 200:
        show_snack("Failed to sync worker")
        return
    show_snack("Worker synced successfully")
    

def submit_worker_password_data(data, wrk_id):
    show_snack("Please wait as worker password is edited")
    Thread(target=edit_password, args=(data, wrk_id), daemon=True).start()

def edit_password(data, wrk_id):
    url = f"{SERVER_URL}workers/workers-change-password/?hospital_id={store.get('hospital')['hsp_id']}&worker_id={wrk_id}"
    response = requests.put(url, json=data)
    if response.status_code != 200:
        show_snack("Failed to sync worker password")
        return
    show_snack("Worker password synced successfully")

def start_worker_deletion(wrk_id):
    show_snack("Please wait as worker is deleted")
    Thread(target=delete_worker, args=(wrk_id,), daemon=True).start()

def delete_worker(wrk_id):
    url = f"{SERVER_URL}workers/workers-delete/?hospital_id={store.get('hospital')['hsp_id']}&worker_id={wrk_id}"
    response = requests.delete(url)
    if response.status_code != 200:
        show_snack("Failed to sync worker")
        return
    show_snack("Worker synced successfully")

def start_worker_signin(worker_data: dict, callback=None):
    show_snack("Logging in...")
    Thread(target=signin_thread, args=(worker_data, callback), daemon=True).start()

def signin_thread(wrk_data, callback):
    url = f"{SERVER_URL}workers/workers-signin/?hospital_id={store.get('hospital')['hsp_id']}"
    response = requests.post(url, json=wrk_data)
    if response.status_code != 200:
        show_snack("Login Failed")
        return
    
    show_snack("Login Successful")
    
    if callback:
        Clock.schedule_once(lambda dt: callback())
    

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

def fill_role_field(val, target_field, menu):
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