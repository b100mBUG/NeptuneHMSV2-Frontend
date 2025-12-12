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


class TestsRow(MDListItem):
    test_name = StringProperty("")
    test_desc = StringProperty("")
    test_price = StringProperty("")
    show_profile = ObjectProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.radius = (20,)

        self.on_release = lambda: self.show_profile()

        self.name_label = MDListItemHeadlineText(theme_text_color = "Custom", text_color = "blue")
        self.desc_label = MDListItemSupportingText(theme_text_color = "Custom", text_color = "blue")
        self.price_label = MDListItemTertiaryText(theme_text_color = "Custom", text_color = "blue")
        
        self.add_widget(MDListItemLeadingIcon(icon="flask", theme_icon_color = "Custom", icon_color = "blue"))
        self.add_widget(self.name_label)
        self.add_widget(self.desc_label)
        self.add_widget(self.price_label)
        
        self.bind(test_name=lambda inst, val: setattr(self.name_label, 'text', val))
        self.bind(test_desc=lambda inst, val: setattr(self.desc_label, 'text', val))
        self.bind(test_price=lambda inst, val: setattr(self.price_label, 'text', val))

def make_display_label(text, color="blue"):
    lbl = MDLabel(
        text=text,
        theme_text_color="Custom",
        text_color=color,
        halign="left",
        adaptive_height = True,
    )
    return lbl

store = STORE

def display_tests_info(
    test_data: dict,
):
    name_box = MDBoxLayout(spacing = dp(5), adaptive_height=True)
    name_box.add_widget(MDIcon(icon="flask", pos_hint = {"top":1}, theme_icon_color = "Custom", icon_color = "blue"))
    name_box.add_widget(make_display_label(f"Test: {test_data.get('test_name', "Unknown").upper()}"))

    desc_box = MDBoxLayout(spacing = dp(5), adaptive_height=True)
    desc_box.add_widget(MDIcon(icon="information-outline", pos_hint = {"top":1}, theme_icon_color = "Custom", icon_color = "blue"))
    desc_box.add_widget(make_display_label(f"Description: {test_data.get('test_desc', "unknown")}"))
    
    price_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    price_box.add_widget(MDIcon(icon="currency-usd", theme_icon_color = "Custom", icon_color = "blue"))
    price_box.add_widget(make_display_label(f"Price: Ksh. {test_data.get('test_price', "unknown")}"))

    date_box = MDBoxLayout(spacing = dp(5), size_hint_y = None, height = dp(40))
    date_box.add_widget(MDIcon(icon="calendar", theme_icon_color = "Custom", icon_color = "blue"))
    date_box.add_widget(make_display_label(f"Added On: {test_data.get('date_added', "YY-MM-DD")}"))
    
    grid = MDGridLayout(size_hint_y = None, adaptive_height = True, cols=1, padding = dp(10), spacing = dp(10))
    scroll = MDScrollView()
    scroll.add_widget(grid)
    
    grid.add_widget(Widget(size_hint_y = None, height = dp(20)))
    grid.add_widget(name_box)
    grid.add_widget(desc_box)
    grid.add_widget(price_box)

    grid.add_widget(date_box)
    
    return scroll

def fetch_tests(intent="all", sort_term="all", sort_dir="desc", search_term="ss", callback=None):
    Thread(target=fetch_and_return_online_tests, args=(intent, sort_term, sort_dir, search_term, callback), daemon=True).start()

def fetch_and_return_online_tests(intent, sort_term, sort_dir, search_term, callback):
    url = ""
    if intent == "search":
        url = f"{SERVER_URL}lab_tests/lab_tests-search/?hospital_id={store.get('hospital')['hsp_id']}&search_term={search_term}"
    elif intent == "all":
        url = f"{SERVER_URL}lab_tests/lab_tests-fetch/?hospital_id={store.get('hospital')['hsp_id']}&sort_term={sort_term}&sort_dir={sort_dir}"

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

def tests_add_form():
    test_name = MDTextField(
        MDTextFieldHintText(text = "Test"),
        MDTextFieldLeadingIcon(icon="flask")
    )
    test_desc = MDTextField(
        MDTextFieldHintText(text = "Description"),
        MDTextFieldLeadingIcon(icon="information-outline")
    )
    test_price = MDTextField(
        MDTextFieldHintText(text = "Price"),
        MDTextFieldLeadingIcon(icon="currency-usd")
    )
    
    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(test_name)
    content.add_widget(test_desc)
    content.add_widget(test_price)
    
    test_dialog = MDDialog(
        MDDialogIcon(icon = "flask", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Add Test", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_test_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: test_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    test_dialog.open()
    
    def prepare_test_data():
        if not test_name.text.strip():
            show_snack("Enter test name")
            return
        if not test_desc.text.strip():
            show_snack("Enter test description")
            return
        if not test_price.text.strip():
            show_snack("Enter test price")
            return
        
        data = {
            "test_name": test_name.text.strip(),
            'test_desc': test_desc.text.strip(),
            'test_price': float(test_price.text.strip())
        }
        submit_test_data(data)
def submit_test_data(data):
    show_snack("Please wait as test is added")
    Thread(target=add_test, args=(data,), daemon=True).start()

def add_test(data):
    url = f"{SERVER_URL}lab_tests/lab_tests-add/?hospital_id={store.get('hospital')['hsp_id']}"
    response = requests.post(url, json=data)
    if response.status_code != 200:
        show_snack("Failed to sync test")
        return
    show_snack("Test synced successfully")

def make_text_field(field_name, field_icon, field_text=None):
    text_field = MDTextField(
        MDTextFieldHintText(text=field_name),
        MDTextFieldLeadingIcon(icon=field_icon),
        text=str(field_text or "")
    )
    return text_field

def test_edit_form(test: dict):
    test_name = make_text_field("Test", "flask", test.get("test_name", None))
    test_desc = make_text_field("Description", "information-outline", test.get("test_desc", None))
    test_price = make_text_field("Price", "currency-usd", test.get("test_price", None))   

    content = MDDialogContentContainer(orientation = "vertical", spacing = dp(10))
    content.add_widget(test_name)
    content.add_widget(test_desc)
    content.add_widget(test_price)

    test_edit_dialog = MDDialog(
        MDDialogIcon(icon = "flask", theme_icon_color="Custom", icon_color="blue"),
        MDDialogHeadlineText(text = "Edit Test", bold=True, theme_text_color="Custom", text_color="blue"),
        content,
        MDDialogButtonContainer(
            Widget(),
            MDIconButton(
                icon="check", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "blue",
                on_release = lambda *a: prepare_test_data()
            ),
            MDIconButton(
                icon="close", 
                theme_icon_color="Custom", 
                icon_color="white",
                theme_bg_color = "Custom",
                md_bg_color = "red",
                on_release = lambda *a: test_edit_dialog.dismiss()
            ),
            spacing = dp(10),
            padding = dp(10),
        ),
        auto_dismiss = False
    )
    test_edit_dialog.open()
    

    def prepare_test_data():
        
        data = {
            "test_name": test_name.text.strip(),
            'test_desc': test_desc.text.strip(),
            'test_price': float(test_price.text.strip()),
        }
        submit_test_edit_data(data, test.get("test_id"))

def confirm_deletion_form(test_id):
    confirm_delete_dialog = MDDialog(
        MDDialogIcon(icon="trash-can", theme_icon_color="Custom", icon_color="red"),
        MDDialogHeadlineText(text="Delete Test", theme_text_color="Custom", text_color="red"),
        MDDialogContentContainer(
            MDLabel(
                text = "Deleting a test is an irreversible process. Are you sure you wish to procede?",
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
                on_release = lambda *a: start_test_deletion(test_id)
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

def submit_test_edit_data(data, test_id):
    show_snack("Please wait as test is edited")
    Thread(target=edit_test, args=(data, test_id), daemon=True).start()

def edit_test(data, test_id):
    url = f"{SERVER_URL}lab_tests/lab_tests-edit/?hospital_id={store.get('hospital')['hsp_id']}&lab_test_id={test_id}"
    response = requests.put(url, json=data)
    print(data)
    if response.status_code != 200:
        show_snack("Failed to sync test")
        return
    show_snack("Test synced successfully. You can refresh the page to view them")

def start_test_deletion(test_id):
    show_snack("Please wait as test is deleted")
    Thread(target=delete_test, args=(test_id,), daemon=True).start()

def delete_test(test_id):
    url = f"{SERVER_URL}lab_tests/lab_tests-delete/?hospital_id={store.get('hospital')['hsp_id']}&lab_test_id={test_id}"
    response = requests.delete(url)
    if response.status_code != 200:
        show_snack("Failed to sync test")
        return
    show_snack("Test synced successfully")

@mainthread
def show_snack(text):
    MDSnackbar(
        MDSnackbarText(text=text), 
        pos_hint={'center_x': 0.5}, 
        size_hint_x=0.5, 
        orientation='horizontal'
    ).open()