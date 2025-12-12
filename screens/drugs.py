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

class DrugsRow(MDListItem):
    drug_name = StringProperty("")
    drug_category = StringProperty("")
    drug_quantity = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.category_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.quantity_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="pill", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.category_label)
        self.add_widget(self.quantity_label)
        
        self.bind(drug_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(drug_category=lambda inst, val: setattr(self.category_label, 'text', val))
        self.bind(drug_quantity=lambda inst, val: setattr(self.quantity_label, 'text', val))

def make_display_label(text):
    return MDLabel(
        text = text,
        theme_text_color = "Custom",
        text_color = "blue"
    )

store = STORE

def display_drugs_info(
    drug_data: dict,
):
    name_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    name_box.add_widget(MDIcon(icon="pill", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    name_box.add_widget(make_display_label(f"   Drug: {drug_data.get('drug_name', "Unknown").upper()}"))

    category_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    category_box.add_widget(MDIcon(icon="shape", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    category_box.add_widget(make_display_label(f"   Category: {drug_data.get('drug_category', "unknown")}"))
    
    description_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    description_box.add_widget(MDIcon(icon="information-outline", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    description_box.add_widget(make_display_label(f"   Description: {drug_data.get('drug_desc', "unknown")}"))
    
    quantity_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    quantity_box.add_widget(MDIcon(icon="counter", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    quantity_box.add_widget(make_display_label(text = f"   Quantity: {drug_data.get('drug_quantity', 0)}"))
    
    price_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    price_box.add_widget(MDIcon(icon="currency-usd", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    price_box.add_widget(make_display_label(text = f"   Price: {drug_data.get('drug_price', 0.0)}"))
    
    expiry_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    expiry_box.add_widget(MDIcon(icon="calendar-clock", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    expiry_box.add_widget(make_display_label(text = f"   Expires on: {drug_data.get('drug_expiry', "YY-MM-DD")}"))
    
    status_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    status_box.add_widget(
        MDIcon(
            icon="check" if datetime.strptime(drug_data.get("drug_expiry"), "%Y-%m-%d") > datetime.today() else "cancel", 
            pos_hint = {"center_y":.5}, 
            theme_icon_color = "Custom", 
            icon_color = "green" if datetime.strptime(drug_data.get("drug_expiry"), "%Y-%m-%d") > datetime.today() else "red"
        )
    )
    status_box.add_widget(
        MDLabel(
            text = "Safe to use" if datetime.strptime(drug_data.get("drug_expiry"), "%Y-%m-%d") > datetime.today() else "Expired",
            theme_text_color = "Custom",
            text_color = "green" if datetime.strptime(drug_data.get("drug_expiry"), "%Y-%m-%d") > datetime.today() else "red"
        )
    )
    sufficient_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    sufficient_box.add_widget(
        MDIcon(
            icon="check" if drug_data.get("drug_quantity") > 0 else "cancel", 
            pos_hint = {"center_y":.5}, 
            theme_icon_color = "Custom", 
            icon_color = "green" if drug_data.get("drug_quantity") > 0 else "red"
        )
    )
    sufficient_box.add_widget(
        MDLabel(
            text = "Sufficient" if drug_data.get("drug_quantity") > 0 else "Depleted",
            theme_text_color = "Custom",
            text_color = "green" if drug_data.get("drug_quantity") > 0 else "red"
        )
    )
    
    date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    date_box.add_widget(MDIcon(icon="calendar", pos_hint = {"center_y":.5}, theme_icon_color = "Custom", icon_color = "blue"))
    date_box.add_widget(make_display_label(f"   Added On: {drug_data.get('date_added', "YY-MM-DD")}"))
    
    grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
    scroll = MDScrollView()
    scroll.add_widget(grid)
    
    grid.add_widget(Widget(size_hint_y = None, height = dp(10)))
    grid.add_widget(name_box)
    grid.add_widget(category_box)
    grid.add_widget(description_box)
    grid.add_widget(quantity_box)
    grid.add_widget(price_box)
    grid.add_widget(expiry_box)
    grid.add_widget(status_box)
    grid.add_widget(sufficient_box)
    grid.add_widget(date_box)
    
    return scroll

def fetch_drugs(intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
    Thread(target=fetch_and_return_online_drugs, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

def fetch_and_return_online_drugs(intent, sort_term, sort_dir, search_term, callback):
    url = ""
    if intent == "search":
        url = f"{SERVER_URL}drugs/drugs-search/?hospital_id={store.get('hospital')['hsp_id']}&search_term={search_term}"
    elif intent == "all":
        url = f"{SERVER_URL}drugs/drugs-fetch/?hospital_id={store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

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

def drugs_add_form():
    drug_name = MDTextField(
        MDTextFieldHintText(text = "Drug"),
        MDTextFieldLeadingIcon(icon="pill")
    )
    drug_cat = MDTextField(
        MDTextFieldHintText(text = "Category"),
        MDTextFieldLeadingIcon(icon="shape")
    )
    drug_qty = MDTextField(
        MDTextFieldHintText(text = "Quantity"),
        MDTextFieldLeadingIcon(icon="counter")
    )
    drug_price = MDTextField(
        MDTextFieldHintText(text = "Price"),
        MDTextFieldLeadingIcon(icon="currency-usd")
    )
    drug_expiry = MDTextField(
        MDTextFieldHintText(text = "Expiry"),
        MDTextFieldLeadingIcon(icon="calendar-clock")
    )
    
    exp_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    exp_box.add_widget(drug_expiry)
    exp_box.add_widget(MDIconButton(icon="calendar", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: show_date_picker(drug_expiry)))
    
    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(drug_name)
    content.add_widget(drug_cat)
    content.add_widget(drug_qty)
    content.add_widget(drug_price)
    content.add_widget(exp_box)
    
    drug_dialog = MDDialog(
        MDDialogIcon(icon = "pill", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Add Drug", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_drug_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: drug_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    drug_dialog.open()
    
    def prepare_drug_data():
        if not drug_name.text.strip():
            show_snack("Enter drug name")
            return
        if not drug_cat.text.strip():
            show_snack("Enter drug category")
            return
        if not drug_qty.text.strip():
            show_snack("Enter drug quantity")
            return
        if not drug_price.text.strip():
            show_snack("Enter drug price")
            return
        if not drug_expiry.text.strip():
            show_snack("Enter drug expiry")
            return
        drug_exp_str = drug_expiry.text.strip()
        try:
            drug_exp = datetime.strptime(drug_exp_str, "%Y-%m-%d")
        except Exception as e:
            show_snack("Invalid date passed")
            return
        
        data = {
            "drug_name": drug_name.text.strip(),
            'drug_category': drug_cat.text.strip(),
            'drug_quantity': drug_qty.text.strip(),
            'drug_price': drug_price.text.strip(),
            'drug_expiry': drug_exp.strftime("%Y-%m-%d"),
        }
        submit_drug_data(data)
def submit_drug_data(data):
    show_snack("Please wait as drug is added")
    Thread(target=add_drug, args=(data,), daemon=True).start()

def add_drug(data):
    url = f"{SERVER_URL}drugs/drugs-add/?hospital_id={store.get('hospital')['hsp_id']}"
    response = requests.post(url, json=data)
    if response.status_code != 200:
        show_snack("Failed to sync drug")
        return
    show_snack("Drug synced successfully")

def make_text_field(field_name, field_icon, field_text=None):
    text_field = MDTextField(
        MDTextFieldHintText(text=field_name),
        MDTextFieldLeadingIcon(icon=field_icon),
        text=str(field_text or "")
    )
    return text_field

def drug_edit_form(drug: dict):
    drug_name = make_text_field("Drug", "pill", drug.get("drug_name", None))
    drug_category = make_text_field("Category", "shape", drug.get("drug_category", None))
    drug_desc = make_text_field("Description", "information-outline", drug.get("drug_desc", None))
    drug_quantity = make_text_field("Quantity", "counter", drug.get("drug_quantity", None))   
    drug_price = make_text_field("Price", "currency-usd", drug.get("drug_price", None))   
    drug_expiry = make_text_field("Expiry", "calendar-clock", drug.get("drug_expiry", None))   

    exp_box = MDBoxLayout(size_hint_y = None, height = dp(60), spacing = dp(5))
    exp_box.add_widget(drug_expiry)
    exp_box.add_widget(MDIconButton(icon="calendar", theme_icon_color="Custom", icon_color="blue", on_release=lambda *a: show_date_picker(drug_expiry)))

    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(drug_name)
    content.add_widget(drug_category)
    content.add_widget(drug_desc)
    content.add_widget(drug_quantity)
    content.add_widget(drug_price)
    content.add_widget(exp_box)
    
    drug_edit_dialog = MDDialog(
        MDDialogIcon(icon = "pill", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Edit Drug", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_drug_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: drug_edit_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    drug_edit_dialog.open()
    

    def prepare_drug_data():
        
        drug_exp_str = drug_expiry.text.strip()
        try:
            drug_exp = datetime.strptime(drug_exp_str, "%Y-%m-%d")
        except Exception as e:
            show_snack("Invalid date passed")
            return
        
        data = {
            "drug_name": drug_name.text.strip(),
            'drug_category': drug_category.text.strip(),
            'drug_quantity': int(drug_quantity.text.strip()),
            'drug_price': float(drug_price.text.strip()),
            'drug_expiry': drug_exp.strftime("%Y-%m-%d"),
        }
        submit_drug_edit_data(data, drug.get("drug_id"))

def confirm_deletion_form(drug_id):
    confirm_delete_dialog = MDDialog(
        MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
        MDDialogHeadlineText(text="Delete Drug", theme_text_color="Custom", text_color="red"),
        MDDialogContentContainer(
            MDLabel(
                text = "Deleting a drug is an irreversible process. Are you sure you wish to procede?",
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
                on_release = lambda *a: start_drug_deletion(drug_id)
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

def submit_drug_edit_data(data, drug_id):
    show_snack("Please wait as worker is edited")
    Thread(target=edit_drug, args=(data, drug_id), daemon=True).start()

def edit_drug(data, drug_id):
    url = f"{SERVER_URL}drugs/drugs-edit/?hospital_id={store.get('hospital')['hsp_id']}&drug_id={drug_id}"
    response = requests.put(url, json=data)
    if response.status_code != 200:
        show_snack("Failed to sync drug")
        return
    show_snack("Drug synced successfully")

def start_drug_deletion(drug_id):
    show_snack("Please wait as worker is deleted")
    Thread(target=delete_drug, args=(drug_id,), daemon=True).start()

def delete_drug(drug_id):
    url = f"{SERVER_URL}drugs/drugs-delete/?hospital_id={store.get('hospital')['hsp_id']}&drug_id={drug_id}"
    response = requests.delete(url)
    if response.status_code != 200:
        show_snack("Failed to sync drug")
        return
    show_snack("Drug synced successfully")

def start_drug_sale(drug_data: dict):
    show_snack("Starting drug selling process...")
    Thread(target=sale_drug, args=(drug_data,), daemon=True).start()

def sale_drug(drug_data: dict):
    url = f"{SERVER_URL}drugs/drugs/drug-sale?hospital_id={store.get('hospital')['hsp_id']}&drug_id={drug_data.get('drug_id')}&drug_qty={drug_data.get('qty')}"
    response = requests.put(url)
    if response.status_code != 200:
        show_snack("Failed to sync drug")
        return
    show_snack("Drugs synced successfully")

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


@mainthread
def show_snack(text):
    MDSnackbar(
        MDSnackbarText(text=text), 
        pos_hint={'center_x': 0.5}, 
        size_hint_x=0.5, 
        orientation='horizontal'
    ).open()