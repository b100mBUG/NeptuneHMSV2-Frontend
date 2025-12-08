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
from database.actions import service

class ServicesRow(MDListItem):
    service_name = StringProperty("")
    service_desc = StringProperty("")
    service_price = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.desc_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.price_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="toolbox", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.desc_label)
        self.add_widget(self.price_label)
        
        self.bind(service_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(service_desc=lambda inst, val: setattr(self.desc_label, 'text', val))
        self.bind(service_price=lambda inst, val: setattr(self.price_label, 'text', val))

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

def display_services_info(
    service_data: dict,
):
    name_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    name_box.add_widget(MDIcon(icon="toolbox", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    name_box.add_widget(make_display_label(f"   Service: {service_data.get('service_name', "Unknown").upper()}"))

    desc_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    desc_box.add_widget(MDIcon(icon="information-outline", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    desc_box.add_widget(make_display_label(f"   Description: {service_data.get('service_desc', "unknown")}"))
    
    price_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    price_box.add_widget(MDIcon(icon="currency-usd", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    price_box.add_widget(make_display_label(f"   Price: Ksh. {service_data.get('service_price', "unknown")}"))

    date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    date_box.add_widget(make_display_label(f"   Added On: {service_data.get('date_added', "YY-MM-DD")}"))
    
    grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
    scroll = MDScrollView()
    scroll.add_widget(grid)
    
    grid.add_widget(Widget(size_hint_y = None, height = dp(10)))
    grid.add_widget(name_box)
    grid.add_widget(desc_box)
    grid.add_widget(price_box)

    grid.add_widget(date_box)
    
    return scroll

def fetch_services(intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
    #Thread(target=fetch_and_return_online_services, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()
    Thread(target=fetch_and_return_offline_services, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

def fetch_and_return_online_services(intent, sort_term, sort_dir, search_term, callback):
    url = ""
    if intent == "search":
        url = f"{SERVER_URL}services/services-search/?hospital_id={store.get('hospital')['hsp_id']}&search_term={search_term}"
    elif intent == "all":
        url = f"{SERVER_URL}services/services-fetch/?hospital_id={store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
        else:
            data = None
    except Exception:
        data = None

    if callback:
        run_on_main_thread(callback, data)

def fetch_and_return_offline_services(intent, sort_term, sort_dir, search_term, callback):
    try:
        if intent == "all":
            db_result = asyncio.run(service.fetch_services(store.get('hospital')['hsp_id'], sort_term, sort_dir))
        elif intent == "search":
            db_result = asyncio.run(service.search_services(store.get('hospital')['hsp_id'], search_term))
        data = [
            {
                "service_id": service.service_id,
                "hospital_id": service.hospital_id,
                "service_name": service.service_name,
                "service_desc": service.service_desc,
                "service_price": service.service_price,
                "date_added": service.date_added
            } for service in db_result
        ]
    except Exception:
        data = None

    if callback:
        run_on_main_thread(callback, data)

@mainthread
def run_on_main_thread(callback, data):
    callback(data)

def services_add_form():
    service_name = MDTextField(
        MDTextFieldHintText(text = "Service"),
        MDTextFieldLeadingIcon(icon="toolbox")
    )
    service_desc = MDTextField(
        MDTextFieldHintText(text = "Description"),
        MDTextFieldLeadingIcon(icon="information-outline")
    )
    service_price = MDTextField(
        MDTextFieldHintText(text = "Price"),
        MDTextFieldLeadingIcon(icon="currency-usd")
    )
    
    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(service_name)
    content.add_widget(service_desc)
    content.add_widget(service_price)
    
    service_dialog = MDDialog(
        MDDialogIcon(icon = "toolbox", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Add Service", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_service_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: service_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    service_dialog.open()
    
    def prepare_service_data():
        if not service_name.text.strip():
            show_snack("Enter service name")
            return
        if not service_desc.text.strip():
            show_snack("Enter service description")
            return
        if not service_price.text.strip():
            show_snack("Enter service price")
            return
        
        data = {
            "service_name": service_name.text.strip(),
            'service_desc': service_desc.text.strip(),
            'service_price': float(service_price.text.strip())
        }
        submit_service_data(data)
def submit_service_data(data):
    show_snack("Please wait as service is added")
    Thread(target=add_service, args=(data,), daemon=True).start()

def add_service(data):
    #url = f"{SERVER_URL}services/services-add/?hospital_id={store.get('hospital')['hsp_id']}"
    #response = requests.post(url, json=data)
    #if response.status_code != 200:
        #show_snack("Failed to add service")
        #return
    #show_snack("Service added successfully. You can refresh the page to view them")
    try:
        asyncio.run(service.add_services(store.get('hospital')['hsp_id'], data))
        show_snack("Service added successfully")
    except Exception as e:
        show_snack("An unexpected error occurred. Please try again.")
        return

def make_text_field(field_name, field_icon, field_text=None):
    text_field = MDTextField(
        MDTextFieldHintText(text=field_name),
        MDTextFieldLeadingIcon(icon=field_icon),
        text=str(field_text or "")
    )
    return text_field

def service_edit_form(service: dict):
    service_name = make_text_field("Service", "toolbox", service.get("service_name", None))
    service_desc = make_text_field("Description", "information-outline", service.get("service_desc", None))
    service_price = make_text_field("Price", "currency-usd", service.get("service_price", None))   

    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(service_name)
    content.add_widget(service_desc)
    content.add_widget(service_price)

    service_edit_dialog = MDDialog(
        MDDialogIcon(icon = "toolbox", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Edit Service", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_service_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: service_edit_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    service_edit_dialog.open()
    

    def prepare_service_data():
        
        data = {
            "service_name": service_name.text.strip(),
            'service_desc': service_desc.text.strip(),
            'service_price': float(service_price.text.strip()),
        }
        submit_service_edit_data(data, service.get("service_id"))

def confirm_deletion_form(service_id):
    confirm_delete_dialog = MDDialog(
        MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
        MDDialogHeadlineText(text="Delete Service", theme_text_color="Custom", text_color="red"),
        MDDialogContentContainer(
            MDLabel(
                text = "Deleting a service is an irreversible process. Are you sure you wish to procede?",
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
                on_release = lambda *a: start_service_deletion(service_id)
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

def submit_service_edit_data(data, service_id):
    show_snack("Please wait as service is edited")
    Thread(target=edit_service, args=(data, service_id), daemon=True).start()

def edit_service(data, service_id):
    #url = f"{SERVER_URL}services/services-edit/?hospital_id={store.get('hospital')['hsp_id']}&service_id={service_id}"
    #response = requests.put(url, json=data)
    #if response.status_code != 200:
        #show_snack("Failed to edit service")
        #return
    #show_snack("Service edited successfully. You can refresh the page to view them")
    try:
        asyncio.run(service.edit_service(store.get('hospital')['hsp_id'], service_id, data))
        show_snack("Service edited successfully.")
    except Exception as e:
        show_snack("An unexpected error occurred. Please try again")
        return

def start_service_deletion(service_id):
    show_snack("Please wait as service is deleted")
    Thread(target=delete_service, args=(service_id,), daemon=True).start()

def delete_service(service_id):
    #url = f"{SERVER_URL}services/services-delete/?hospital_id={store.get('hospital')['hsp_id']}&service_id={service_id}"
    #response = requests.delete(url)
    #if response.status_code != 200:
        #show_snack("Failed to delete service")
        #return
   # show_snack("Service deleted successfully. You can refresh the page to view them")
    try: 
        asyncio.run(service.delete_service(store.get('hospital')['hsp_id'], service_id))
        show_snack("Service deleted successfully")
    except Exception as e:
        show_snack("An unexpected error occurred. Please try again")
        return
        
@mainthread
def show_snack(text):
    MDSnackbar(
        MDSnackbarText(text=text), 
        pos_hint={'center_x': 0.5}, 
        size_hint_x=0.5, 
        orientation='horizontal'
    ).open()